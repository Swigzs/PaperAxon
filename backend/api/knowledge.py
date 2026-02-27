"""知识图谱与热度 API。"""
from fastapi import APIRouter

from backend.db import get_conn
from backend.db import models as db
from backend.services.knowledge_graph import build_graph, get_trending

router = APIRouter(tags=["knowledge"])


@router.get("/api/knowledge-graph")
def knowledge_graph():
    conn = get_conn()
    try:
        nodes, edges = build_graph(conn)
        return {"nodes": nodes, "edges": edges}
    finally:
        conn.close()


@router.get("/api/trending")
def trending():
    conn = get_conn()
    try:
        items = get_trending(conn, limit=20)
        return {"items": items}
    finally:
        conn.close()
