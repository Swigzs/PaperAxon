"""PDF 解析：PyMuPDF 提取文本与基础结构。"""
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF


def parse_pdf(pdf_path: str | Path) -> dict[str, Any]:
    """
    解析 PDF，返回统一结构：title, authors, abstract, keywords, sections, raw_text。
    V0.1 简化：从首页和后续页提取文本，尝试识别标题与摘要。
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    doc = fitz.open(path)
    try:
        full_text_parts = []
        # 尝试取首页前几段作为标题/摘要（启发式）
        title = ""
        abstract = ""
        for i, page in enumerate(doc):
            text = page.get_text()
            full_text_parts.append(text)
            if i == 0:
                blocks = text.strip().split("\n\n")
                if blocks:
                    title = blocks[0].strip()[:500]
                if len(blocks) > 1:
                    abstract = "\n\n".join(blocks[1:4])[:3000]
        raw_text = "\n\n".join(full_text_parts)
        # 若未识别到摘要，用前 3000 字
        if not abstract and raw_text:
            abstract = raw_text[:3000]
        return {
            "title": title or "Untitled",
            "authors": "",
            "abstract": abstract,
            "keywords": [],
            "sections": [],
            "raw_text": raw_text[:50000],
        }
    finally:
        doc.close()
