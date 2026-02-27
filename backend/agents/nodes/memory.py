"""记忆节点：将论文元信息与解读路径写入 SQLite 与文件。"""
from pathlib import Path

from backend.agents.state import AgentState
from backend.config import INTERPRETATIONS_DIR
from backend.db import get_conn
from backend.db import models as db


def run(state: AgentState) -> AgentState:
    if state.get("error"):
        return state
    paper_id = state.get("paper_id")
    interpretation = state.get("interpretation")
    parse_result = state.get("parse_result") or {}
    if not paper_id or not interpretation:
        return {**state, "error": "缺少 paper_id 或 interpretation"}

    conn = get_conn()
    try:
        content_path = str(INTERPRETATIONS_DIR / f"{paper_id}.md")
        Path(content_path).parent.mkdir(parents=True, exist_ok=True)
        Path(content_path).write_text(interpretation, encoding="utf-8")
        db.interpretation_upsert(conn, paper_id, content_path)
        return {**state, "memory_updated": True}
    except Exception as e:
        return {**state, "error": str(e)}
    finally:
        conn.close()
