"""数据库初始化与连接。"""
import sqlite3
from pathlib import Path

from backend.config import DB_PATH
from backend.db.models import create_tables, get_conn as _get_conn


def get_db_path() -> Path:
    return DB_PATH


def init_db() -> None:
    """确保数据目录存在并创建/迁移表。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    create_tables()


def get_conn() -> sqlite3.Connection:
    return _get_conn()
