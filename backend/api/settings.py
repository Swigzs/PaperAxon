"""采集设置：是否开启、采集时间。"""
from fastapi import APIRouter
from pydantic import BaseModel

from backend.db import get_conn
from backend.db import models as db
from backend.config import DEFAULT_COLLECT_TIME

router = APIRouter(prefix="/api/settings", tags=["settings"])


class CollectSettings(BaseModel):
    auto_collect_enabled: bool = False
    collect_time: str = DEFAULT_COLLECT_TIME  # "HH:mm"


@router.get("/collect")
def get_collect_settings():
    conn = get_conn()
    try:
        enabled = db.setting_get(conn, "auto_collect_enabled")
        time_val = db.setting_get(conn, "collect_time") or DEFAULT_COLLECT_TIME
        return {
            "auto_collect_enabled": enabled == "true" if enabled else False,
            "collect_time": time_val,
        }
    finally:
        conn.close()


@router.put("/collect")
def update_collect_settings(body: CollectSettings):
    conn = get_conn()
    try:
        db.setting_set(conn, "auto_collect_enabled", "true" if body.auto_collect_enabled else "false")
        db.setting_set(conn, "collect_time", body.collect_time)
        return {"ok": True}
    finally:
        conn.close()
