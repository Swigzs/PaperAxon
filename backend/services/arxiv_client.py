"""arXiv API：拉取元数据并下载 PDF 到 data/papers/。"""
import re
from pathlib import Path
from typing import Any, Optional

import arxiv
import requests

from backend.config import PAPERS_DIR


def extract_arxiv_id(url_or_id: str) -> Optional[str]:
    """从 URL 或 ID 解析出 arXiv ID，如 2301.12345 或 2301.12345v1。"""
    s = url_or_id.strip()
    # 格式: 2301.12345 或 cs/23010123 等
    m = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", s)
    if m:
        return m.group(1)
    if "arxiv.org" in s:
        m = re.search(r"arxiv\.org/(?:abs|pdf)/([^\s/]+)", s)
        if m:
            return m.group(1).replace(".pdf", "").split("v")[0]
    return None


def fetch_and_download(arxiv_id: str) -> tuple[dict[str, Any], Path]:
    """
    拉取 arXiv 元数据并下载 PDF 到 data/papers/，返回 (元数据 dict, 本地 PDF 路径)。
    元数据含 title, authors, abstract, published_at 等。
    """
    search = arxiv.Search(id_list=[arxiv_id])
    client = arxiv.Client()
    paper = None
    for p in client.results(search):
        paper = p
        break
    if not paper:
        raise ValueError(f"arXiv ID not found: {arxiv_id}")

    # 下载 PDF
    pdf_url = paper.pdf_url
    resp = requests.get(pdf_url, timeout=60)
    resp.raise_for_status()
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    local_path = PAPERS_DIR / f"{arxiv_id.replace('/', '_')}.pdf"
    local_path.write_bytes(resp.content)

    authors_str = ", ".join(a.name for a in paper.authors)
    published = paper.published.strftime("%Y-%m-%dT%H:%M:%SZ") if paper.published else None
    return {
        "arxiv_id": arxiv_id,
        "title": paper.title or "",
        "authors": authors_str,
        "abstract": paper.summary or "",
        "published_at": published,
        "source_path_or_url": str(local_path),
    }, local_path
