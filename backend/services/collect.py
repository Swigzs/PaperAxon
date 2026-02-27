"""每日定时采集 arXiv（近 24h，默认 cat=physics.hist-ph）。"""
from datetime import datetime, timedelta
from typing import Optional

import arxiv

from backend.config import DEFAULT_ARXIV_CATEGORY
from backend.db import get_conn
from backend.db import models as db
from backend.services.arxiv_client import fetch_and_download, extract_arxiv_id


def run_collect(category: Optional[str] = None) -> int:
    """
    执行一次采集：拉取近 24 小时更新的论文，去重后写入 papers。
    返回本次新增条数。
    """
    cat = category or DEFAULT_ARXIV_CATEGORY
    # 近 24 小时：用 arxiv 的 sort_by=lastUpdatedDate，取最近一批
    search = arxiv.Search(
        query=f"cat:{cat}",
        sort_by=arxiv.SortCriterion.LastUpdatedDate,
        max_results=50,
    )
    client = arxiv.Client()
    conn = get_conn()
    new_count = 0
    try:
        for p in client.results(search):
            # 只保留最近 24h 内更新的
            if p.updated:
                from datetime import timezone
                cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
                if p.updated.replace(tzinfo=timezone.utc) < cutoff:
                    continue
            arxiv_id = p.entry_id.split("/")[-1].split("v")[0]
            existing = db.paper_get_by_arxiv_id(conn, arxiv_id)
            if existing:
                continue
            try:
                from nanoid import generate as nanoid_generate
                meta, _ = fetch_and_download(arxiv_id)
                paper_id = nanoid_generate(size=12)
                db.paper_insert(
                    conn, paper_id, "arxiv", meta["source_path_or_url"],
                    title=meta["title"], authors=meta["authors"], abstract=meta["abstract"],
                    arxiv_id=arxiv_id, published_at=meta.get("published_at"),
                )
                new_count += 1
            except Exception:
                continue
        run_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
        db.collect_log_insert(conn, run_at, new_count)
        return new_count
    finally:
        conn.close()
