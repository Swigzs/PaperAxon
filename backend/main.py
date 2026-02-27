"""FastAPI 应用入口：挂载 API、静态资源、定时采集、MCP/Skill 占位。"""
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from backend.config import ensure_data_dirs, PORT, PROJECT_ROOT, DATA_DIR
from backend.db import init_db
from backend.log_config import setup_logging, get_logger
from backend.api.papers import router as papers_router
from backend.api.tasks import router as tasks_router
from backend.api.settings import router as settings_router
from backend.api.knowledge import router as knowledge_router
from backend.services.collect import run_collect
from backend.db import get_conn
from backend.db import models as db


logger = get_logger(__name__)


def _scheduled_collect():
    """每分钟检查：若当前时间与配置的采集时间一致且已开启，则执行采集。"""
    from datetime import datetime
    conn = get_conn()
    try:
        enabled = db.setting_get(conn, "auto_collect_enabled")
        if enabled != "true":
            return
        collect_time = db.setting_get(conn, "collect_time") or "00:00"
        parts = collect_time.split(":")
        target_h, target_m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
        now = datetime.now()
        if now.hour == target_h and now.minute == target_m:
            n = run_collect()
            logger.info("定时采集完成, 新增论文数: %s", n)
    except Exception as e:
        logger.exception("定时采集异常: %s", e)
    finally:
        conn.close()


scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_data_dirs()
    setup_logging()
    logger.info("PaperAxon 启动 data_dir=%s port=%s", DATA_DIR, PORT)
    init_db()
    scheduler.add_job(_scheduled_collect, "interval", minutes=1)
    scheduler.start()
    yield
    scheduler.shutdown()
    logger.info("PaperAxon 关闭")


app = FastAPI(title="PaperAxon", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(papers_router)
app.include_router(tasks_router)
app.include_router(settings_router)
app.include_router(knowledge_router)

# 前端静态资源（生产：build 后放在 frontend/dist）
frontend_dist = PROJECT_ROOT / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=PORT, reload=True)
