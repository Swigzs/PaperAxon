"""知识图谱（NetworkX 内存建图）与热度。"""
import sqlite3
from typing import Any

import networkx as nx


def build_graph(conn: sqlite3.Connection) -> tuple[list[dict], list[dict]]:
    """从 papers 表建图：节点为 paper_id、作者、关键词（简化用 title 词）；边为论文-作者、论文-论文（同分类）。"""
    G = nx.Graph()
    rows = conn.execute("SELECT paper_id, title, authors FROM papers").fetchall()
    for r in rows:
        pid, title, authors = r[0], r[1] or "", r[2] or ""
        G.add_node(pid, type="paper", label=title[:50] or pid)
        for a in authors.split(","):
            a = a.strip()
            if a:
                aid = f"author:{a[:30]}"
                if not G.has_node(aid):
                    G.add_node(aid, type="author", label=a[:30])
                G.add_edge(pid, aid)

    nodes = [{"id": n, "data": dict(G.nodes[n])} for n in G.nodes()]
    edges = [{"source": u, "target": v} for u, v in G.edges()]
    return nodes, edges


def get_trending(conn: sqlite3.Connection, limit: int = 20) -> list[dict[str, Any]]:
    """热度：按 updated_at 降序（最近更新优先）。"""
    rows = conn.execute(
        "SELECT paper_id, title, authors, updated_at FROM papers ORDER BY updated_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [
        {
            "paper_id": r[0],
            "title": r[1],
            "authors": r[2],
            "updated_at": r[3],
        }
        for r in rows
    ]
