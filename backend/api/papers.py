"""论文相关 API：上传、from-arxiv、解读、播客、列表、删除、相关论文。"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from nanoid import generate as nanoid_generate

from backend.config import PAPERS_DIR, INTERPRETATIONS_DIR, PODCASTS_DIR, ensure_data_dirs
from backend.db import get_conn
from backend.db import models as db
from backend.agents.graph import run_interpret, run_podcast_only
from backend.services.arxiv_client import extract_arxiv_id, fetch_and_download
from backend.log_config import get_logger

router = APIRouter(prefix="/api/papers", tags=["papers"])
logger = get_logger(__name__)

# 异步任务在线程池中执行，避免阻塞
_executor = ThreadPoolExecutor(max_workers=4)


def _run_interpret_task(paper_id: str, task_id: str):
    conn = get_conn()
    try:
        db.task_update(conn, task_id, "running")
    finally:
        conn.close()
    try:
        row = db.paper_get_by_id(get_conn(), paper_id)
        conn2 = get_conn()
        try:
            if not row:
                db.task_update(conn2, task_id, "failed", error="论文不存在")
                return
            path = row["source_path_or_url"]
            if path and Path(path).exists():
                result = run_interpret(paper_id, {"path": path})
            else:
                db.task_update(conn2, task_id, "failed", error="PDF 文件不存在")
                return
            err = result.get("error")
            if err:
                db.task_update(conn2, task_id, "failed", error=err)
                return
            interp_row = db.interpretation_get(conn2, paper_id)
            content_path = interp_row["content_path"] if interp_row else str(INTERPRETATIONS_DIR / f"{paper_id}.md")
            db.task_update(conn2, task_id, "success", result={"paper_id": paper_id, "interpretation_path": content_path})
        finally:
            conn2.close()
    except Exception as e:
        logger.exception("解读任务失败 paper_id=%s task_id=%s: %s", paper_id, task_id, e)
        c = get_conn()
        try:
            db.task_update(c, task_id, "failed", error=str(e))
        finally:
            c.close()


def _run_podcast_task(paper_id: str, task_id: str):
    conn = get_conn()
    try:
        db.task_update(conn, task_id, "running")
    finally:
        conn.close()
    try:
        interp_row = db.interpretation_get(get_conn(), paper_id)
        if not interp_row or not interp_row["content_path"]:
            c = get_conn()
            try:
                db.task_update(c, task_id, "failed", error="请先完成解读")
            finally:
                c.close()
            return
        content_path = interp_row["content_path"]
        interpretation = Path(content_path).read_text(encoding="utf-8")
        result = run_podcast_only(paper_id, interpretation)
        err = result.get("error")
        if err:
            c = get_conn()
            try:
                db.task_update(c, task_id, "failed", error=err)
            finally:
                c.close()
            return
        audio_path = result.get("podcast_audio_path", "")
        podcast_url = f"/api/papers/{paper_id}/podcast" if audio_path else ""
        is_placeholder = Path(audio_path).suffix.lower() == ".txt" if audio_path else True
        c = get_conn()
        try:
            db.task_update(
                c, task_id, "success",
                result={"paper_id": paper_id, "podcast_url": podcast_url, "is_placeholder": is_placeholder},
            )
        finally:
            c.close()
    except Exception as e:
        logger.exception("播客任务失败 paper_id=%s task_id=%s: %s", paper_id, task_id, e)
        c = get_conn()
        try:
            db.task_update(c, task_id, "failed", error=str(e))
        finally:
            c.close()


# ---------- 请求体 ----------
class FromArxivBody(BaseModel):
    url: str | None = None
    arxiv_id: str | None = None


# ---------- 上传 PDF ----------
@router.post("/upload")
def upload_pdf(file: UploadFile = File(...)):
    ensure_data_dirs()
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "请上传 PDF 文件")
    paper_id = nanoid_generate(size=12)
    path = PAPERS_DIR / f"{paper_id}.pdf"
    path.write_bytes(file.file.read())
    conn = get_conn()
    try:
        db.paper_insert(
            conn, paper_id, "local_pdf", str(path),
            title=file.filename or "Untitled", authors="", abstract="",
        )
        return {"paper_id": paper_id}
    finally:
        conn.close()


# ---------- 从 arXiv 拉取 ----------
@router.post("/from-arxiv")
def from_arxiv(body: FromArxivBody):
    ensure_data_dirs()
    arxiv_id = body.arxiv_id or (extract_arxiv_id(body.url) if body.url else None)
    if not arxiv_id:
        raise HTTPException(400, "需要 url 或 arxiv_id")

    conn = get_conn()
    try:
        existing = db.paper_get_by_arxiv_id(conn, arxiv_id)
        if existing:
            return {"paper_id": existing["paper_id"]}
    finally:
        conn.close()

    meta, local_path = fetch_and_download(arxiv_id)
    conn = get_conn()
    try:
        paper_id = nanoid_generate(size=12)
        db.paper_insert(
            conn, paper_id, "arxiv", meta["source_path_or_url"],
            title=meta["title"], authors=meta["authors"], abstract=meta["abstract"],
            arxiv_id=arxiv_id, published_at=meta.get("published_at"),
        )
        return {"paper_id": paper_id}
    finally:
        conn.close()


# ---------- 触发解读（异步） ----------
@router.post("/{paper_id}/interpret")
def trigger_interpret(paper_id: str):
    conn = get_conn()
    try:
        row = db.paper_get_by_id(conn, paper_id)
        if not row:
            raise HTTPException(404, "论文不存在")
        task_id = nanoid_generate(size=16)
        db.task_insert(conn, task_id, "interpret")
        _executor.submit(_run_interpret_task, paper_id, task_id)
        return {"task_id": task_id}
    finally:
        conn.close()


# ---------- 获取论文元信息 ----------
@router.get("/{paper_id}")
def get_paper(paper_id: str):
    conn = get_conn()
    try:
        row = db.paper_get_by_id(conn, paper_id)
        if not row:
            raise HTTPException(404, "论文不存在")
        return {
            "paper_id": row["paper_id"],
            "title": row["title"],
            "authors": row["authors"],
            "abstract": row["abstract"],
            "arxiv_id": row["arxiv_id"] or None,
            "source_type": row["source_type"],
            "published_at": row["published_at"] or None,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    finally:
        conn.close()


# ---------- 获取解读正文 ----------
@router.get("/{paper_id}/interpretation")
def get_interpretation(paper_id: str):
    conn = get_conn()
    try:
        row = db.interpretation_get(conn, paper_id)
        if not row:
            raise HTTPException(404, "暂无解读")
        p = Path(row["content_path"])
        if not p.exists():
            raise HTTPException(404, "解读文件不存在")
        return FileResponse(p, media_type="text/markdown")
    finally:
        conn.close()


# ---------- 获取播客音频（支持 GET 与 HEAD；仅 .mp3/.wav 视为可播放，.txt 占位返回 503）----------
@router.api_route("/{paper_id}/podcast", methods=["GET", "HEAD"])
def get_podcast(paper_id: str, request: Request):
    conn = get_conn()
    try:
        row = db.podcast_get(conn, paper_id)
        if not row:
            raise HTTPException(404, "暂无播客")
        p = Path(row["audio_path"])
        if not p.exists():
            txt = p.with_suffix(".txt")
            if txt.exists():
                raise HTTPException(503, "TTS 未配置，仅生成文稿占位")
            raise HTTPException(404, "播客文件不存在")
        # .txt 为 TTS 未配置时的文稿占位，不可播放，统一返回 503
        if p.suffix.lower() == ".txt":
            raise HTTPException(503, "TTS 未配置，仅生成文稿占位；请配置 TTS 后重新生成播客")
        media = "audio/wav" if p.suffix.lower() == ".wav" else "audio/mpeg"
        if request.method == "HEAD":
            return Response(status_code=200, headers={"Content-Type": media})
        return FileResponse(p, media_type=media)
    finally:
        conn.close()


# ---------- 触发播客生成（异步） ----------
@router.post("/{paper_id}/podcast")
def trigger_podcast(paper_id: str):
    conn = get_conn()
    try:
        if not db.paper_get_by_id(conn, paper_id):
            raise HTTPException(404, "论文不存在")
        existing = db.podcast_get(conn, paper_id)
        if existing:
            ap = Path(existing["audio_path"])
            # 仅当存在真实音频文件（.mp3/.wav）时才视为「播客已存在」；.txt 占位允许重新生成
            if ap.exists() and ap.suffix.lower() in (".mp3", ".wav"):
                return {"task_id": None, "message": "播客已存在"}
        task_id = nanoid_generate(size=16)
        db.task_insert(conn, task_id, "podcast")
        _executor.submit(_run_podcast_task, paper_id, task_id)
        return {"task_id": task_id}
    finally:
        conn.close()


# ---------- 论文列表 ----------
@router.get("")
def list_papers(limit: int = 50, offset: int = 0):
    conn = get_conn()
    try:
        rows = db.paper_list(conn, limit=limit, offset=offset)
        return {
            "items": [
                {
                    "paper_id": r["paper_id"],
                    "title": r["title"],
                    "authors": r["authors"],
                    "arxiv_id": r["arxiv_id"] or None,
                    "source_type": r["source_type"],
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"],
                }
                for r in rows
            ],
            "limit": limit,
            "offset": offset,
        }
    finally:
        conn.close()


# ---------- 删除论文 ----------
@router.delete("/{paper_id}")
def delete_paper(paper_id: str):
    conn = get_conn()
    try:
        row = db.paper_get_by_id(conn, paper_id)
        if not row:
            raise HTTPException(404, "论文不存在")
        interp = db.interpretation_get(conn, paper_id)
        podcast = db.podcast_get(conn, paper_id)
        db.paper_delete(conn, paper_id)
        for p in [Path(row["source_path_or_url"]), interp and Path(interp["content_path"]), podcast and Path(podcast["audio_path"])]:
            if p and p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass
        return {"ok": True}
    finally:
        conn.close()


# ---------- 相关论文 ----------
@router.get("/{paper_id}/related")
def get_related(paper_id: str):
    from backend.agents.graph import create_graph
    from backend.agents.state import AgentState
    app = create_graph()
    conn = get_conn()
    try:
        row = db.paper_get_by_id(conn, paper_id)
        if not row:
            raise HTTPException(404, "论文不存在")
        initial: AgentState = {
            "request_type": "related_only",
            "paper_id": paper_id,
            "parse_result": {"title": row["title"], "abstract": row["abstract"]},
        }
        config = {"configurable": {"thread_id": f"related-{paper_id}"}}
        final = None
        for event in app.stream(initial, config):
            for v in event.values():
                final = v
        related = (final or {}).get("related_papers") or []
        if (final or {}).get("error"):
            raise HTTPException(500, final.get("error"))
        return {"items": related}
    finally:
        conn.close()
