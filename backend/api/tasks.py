"""异步任务状态查询。"""
from fastapi import APIRouter, HTTPException

from backend.db import get_conn
from backend.db import models as db

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/{task_id}")
def get_task(task_id: str):
    conn = get_conn()
    try:
        row = db.task_get(conn, task_id)
        if not row:
            raise HTTPException(404, "任务不存在")
        result = db.task_result_parse(row)
        return {
            "task_id": row["task_id"],
            "status": row["status"],
            "result": result,
            "error": row["error"],
        }
    finally:
        conn.close()
