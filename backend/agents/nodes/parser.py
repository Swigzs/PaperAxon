"""解析节点：PDF 或 arXiv 解析，输出 parse_result。"""
from pathlib import Path

from backend.agents.state import AgentState
from backend.services.pdf_parser import parse_pdf
from backend.services import arxiv_client


def run(state: AgentState) -> AgentState:
    paper_input = state.get("paper_input") or {}
    paper_id = state.get("paper_id", "")
    path = paper_input.get("path")
    arxiv_id = paper_input.get("arxiv_id")

    if not path and not arxiv_id and paper_id:
        # 已有 paper_id，从 DB 取路径（由调用方保证 state 中已有 path 或由 API 层注入）
        path = paper_input.get("path")
        if not path:
            return {**state, "error": "缺少 paper_input.path 或 arxiv_id"}

    if arxiv_id:
        try:
            meta, local_path = arxiv_client.fetch_and_download(arxiv_id)
            path = str(local_path)
            # 用元数据补全 parse_result 的 title/authors/abstract
            parse_result = {
                "title": meta["title"],
                "authors": meta["authors"],
                "abstract": meta["abstract"],
                "keywords": [],
                "sections": [],
                "raw_text": meta["abstract"][:8000],
            }
            # 若有本地 PDF 再解析正文
            full_parse = parse_pdf(local_path)
            full_parse["title"] = meta["title"]
            full_parse["authors"] = meta["authors"]
            full_parse["abstract"] = meta["abstract"]
            parse_result = full_parse
            return {**state, "parse_result": parse_result, "paper_input": {**paper_input, "path": path}}
        except Exception as e:
            return {**state, "error": str(e)}

    if path:
        try:
            parse_result = parse_pdf(path)
            return {**state, "parse_result": parse_result}
        except Exception as e:
            return {**state, "error": str(e)}

    return {**state, "error": "需要 paper_input.path 或 paper_input.arxiv_id"}
