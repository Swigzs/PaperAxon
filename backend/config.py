"""配置：数据目录、端口、环境变量。"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录（backend 的上一级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 加载项目根目录下的 .env
load_dotenv(PROJECT_ROOT / ".env")

# 数据目录，可由环境变量 DATA_DIR 覆盖
DATA_DIR = Path(os.environ.get("DATA_DIR", str(PROJECT_ROOT / "data")))
PAPERS_DIR = DATA_DIR / "papers"
INTERPRETATIONS_DIR = DATA_DIR / "interpretations"
PODCASTS_DIR = DATA_DIR / "podcasts"
DB_PATH = DATA_DIR / "paper_axon.db"
LOG_DIR = DATA_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"

# 服务端口
PORT = int(os.environ.get("PORT", "18527"))

# Qwen (DashScope OpenAI 兼容)
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
# 阿里云百炼 base_url（OpenAI 兼容，北京地域；新加坡用 dashscope-intl.aliyuncs.com）
DASHSCOPE_BASE_URL = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
QWEN_MODEL = os.environ.get("QWEN_MODEL", "qwen3-max-2026-01-23")

# TTS（DashScope Qwen TTS；标准 HTTP 接口用 qwen3-tts-flash，realtime 模型需其他接口）
QWEN_TTS_MODEL = os.environ.get("QWEN_TTS_MODEL", "qwen3-tts-flash")

# 阿里云 TTS 旧版预留（若使用独立智能语音服务可配置）
ALIYUN_TTS_APP_KEY = os.environ.get("ALIYUN_TTS_APP_KEY", "")
ALIYUN_TTS_ACCESS_KEY_ID = os.environ.get("ALIYUN_TTS_ACCESS_KEY_ID", "")
ALIYUN_TTS_ACCESS_KEY_SECRET = os.environ.get("ALIYUN_TTS_ACCESS_KEY_SECRET", "")

# 异步任务轮询
TASK_POLL_INTERVAL_SEC = 2
TASK_TIMEOUT_SEC = 15 * 60  # 15 分钟

# 每日采集默认
DEFAULT_COLLECT_TIME = "00:00"
DEFAULT_ARXIV_CATEGORY = "physics.hist-ph"  # 物理史，近 24h


def ensure_data_dirs() -> None:
    """确保 data 及子目录存在。"""
    for d in (DATA_DIR, PAPERS_DIR, INTERPRETATIONS_DIR, PODCASTS_DIR, LOG_DIR):
        d.mkdir(parents=True, exist_ok=True)
