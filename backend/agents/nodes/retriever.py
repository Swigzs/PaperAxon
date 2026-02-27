"""检索节点：用 arXiv API 根据当前论文 title+abstract 查相关论文。"""
import arxiv

from backend.agents.state import AgentState
from backend.db import get_conn
from backend.db import models as db


def run(state: AgentState) -> AgentState:
    if state.get("error"):
        return state
    paper_id = state.get("paper_id")
    parse_result = state.get("parse_result") or {}
    query = (parse_result.get("title") or "") + " " + (parse_result.get("abstract") or "")[:500]
    if not query.strip():
        # 若 state 仅有 paper_id，从 DB 取论文信息
        if paper_id:
            conn = get_conn()
            try:
                row = db.paper_get_by_id(conn, paper_id)
                if row:
                    query = (row["title"] or "") + " " + (row["abstract"] or "")[:500]
            finally:
                conn.close()
    if not query.strip():
        return {**state, "related_papers": [], "next_node": "__end__"}

    try:
        search = arxiv.Search(query=query[:200], max_results=10)
        client = arxiv.Client()
        related = []
        for p in client.results(search):
            related.append({
                "title": p.title,
                "authors": ", ".join(a.name for a in p.authors),
                "arxiv_id": p.entry_id.split("/")[-1],
                "summary": (p.summary or "")[:300],
                "published": p.published.isoformat() if p.published else None,
            })
        return {**state, "related_papers": related, "next_node": "__end__"}
    except Exception as e:
        return {**state, "error": str(e), "related_papers": [], "next_node": "__end__"}
