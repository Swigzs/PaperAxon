"""SQLite 表结构定义与建表。"""
import json
import sqlite3
from datetime import datetime
from typing import Any, Optional

from backend.config import DB_PATH


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(conn: Optional[sqlite3.Connection] = None) -> None:
    close = False
    if conn is None:
        conn = get_conn()
        close = True
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id TEXT NOT NULL UNIQUE,
            source_type TEXT NOT NULL,
            source_path_or_url TEXT NOT NULL,
            title TEXT,
            authors TEXT,
            abstract TEXT,
            arxiv_id TEXT,
            published_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_papers_arxiv_id ON papers(arxiv_id);

        CREATE TABLE IF NOT EXISTS interpretations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id TEXT NOT NULL,
            content_path TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (paper_id) REFERENCES papers(paper_id)
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            result TEXT,
            error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS podcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id TEXT NOT NULL,
            audio_path TEXT NOT NULL,
            duration_sec REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (paper_id) REFERENCES papers(paper_id)
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS collect_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at TEXT NOT NULL,
            new_count INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        """)
        conn.commit()
    finally:
        if close:
            conn.close()


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


# ---------- Paper ----------
def paper_insert(
    conn: sqlite3.Connection,
    paper_id: str,
    source_type: str,
    source_path_or_url: str,
    title: str = "",
    authors: str = "",
    abstract: str = "",
    arxiv_id: Optional[str] = None,
    published_at: Optional[str] = None,
) -> None:
    now = _now()
    conn.execute(
        """INSERT INTO papers (paper_id, source_type, source_path_or_url, title, authors, abstract, arxiv_id, published_at, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (paper_id, source_type, source_path_or_url, title, authors, abstract, arxiv_id or "", published_at or "", now, now),
    )
    conn.commit()


def paper_update_by_arxiv_id(
    conn: sqlite3.Connection,
    arxiv_id: str,
    source_path_or_url: str,
    title: str,
    authors: str,
    abstract: str,
    published_at: Optional[str],
) -> Optional[str]:
    """更新已存在的 arXiv 论文记录，返回 paper_id。"""
    now = _now()
    cur = conn.execute(
        """UPDATE papers SET source_path_or_url=?, title=?, authors=?, abstract=?, published_at=?, updated_at=?
           WHERE arxiv_id=?""",
        (source_path_or_url, title, authors, abstract, published_at or "", now, arxiv_id),
    )
    conn.commit()
    if cur.rowcount:
        row = conn.execute("SELECT paper_id FROM papers WHERE arxiv_id=?", (arxiv_id,)).fetchone()
        return row[0] if row else None
    return None


def paper_get_by_id(conn: sqlite3.Connection, paper_id: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM papers WHERE paper_id=?", (paper_id,)).fetchone()


def paper_get_by_arxiv_id(conn: sqlite3.Connection, arxiv_id: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM papers WHERE arxiv_id=?", (arxiv_id,)).fetchone()


def paper_list(
    conn: sqlite3.Connection,
    limit: int = 50,
    offset: int = 0,
) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM papers ORDER BY updated_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()


def paper_delete(conn: sqlite3.Connection, paper_id: str) -> None:
    conn.execute("DELETE FROM interpretations WHERE paper_id=?", (paper_id,))
    conn.execute("DELETE FROM podcasts WHERE paper_id=?", (paper_id,))
    conn.execute("DELETE FROM papers WHERE paper_id=?", (paper_id,))
    conn.commit()


# ---------- Interpretations ----------
def interpretation_upsert(conn: sqlite3.Connection, paper_id: str, content_path: str) -> None:
    now = _now()
    conn.execute("DELETE FROM interpretations WHERE paper_id=?", (paper_id,))
    conn.execute(
        "INSERT INTO interpretations (paper_id, content_path, created_at) VALUES (?, ?, ?)",
        (paper_id, content_path, now),
    )
    conn.commit()


def interpretation_get(conn: sqlite3.Connection, paper_id: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM interpretations WHERE paper_id=?", (paper_id,)).fetchone()


# ---------- Tasks ----------
def task_insert(conn: sqlite3.Connection, task_id: str, task_type: str) -> None:
    now = _now()
    conn.execute(
        "INSERT INTO tasks (task_id, type, status, result, error, created_at, updated_at) VALUES (?, ?, 'pending', NULL, NULL, ?, ?)",
        (task_id, task_type, now, now),
    )
    conn.commit()


def task_update(conn: sqlite3.Connection, task_id: str, status: str, result: Any = None, error: Optional[str] = None) -> None:
    now = _now()
    result_json = json.dumps(result) if result is not None else None
    conn.execute(
        "UPDATE tasks SET status=?, result=?, error=?, updated_at=? WHERE task_id=?",
        (status, result_json, error, now, task_id),
    )
    conn.commit()


def task_get(conn: sqlite3.Connection, task_id: str) -> Optional[sqlite3.Row]:
    row = conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
    return row


def task_result_parse(row: sqlite3.Row) -> Optional[dict]:
    if row is None or row["result"] is None:
        return None
    try:
        return json.loads(row["result"])
    except Exception:
        return None


# ---------- Podcasts ----------
def podcast_upsert(conn: sqlite3.Connection, paper_id: str, audio_path: str, duration_sec: Optional[float] = None) -> None:
    now = _now()
    conn.execute("DELETE FROM podcasts WHERE paper_id=?", (paper_id,))
    conn.execute(
        "INSERT INTO podcasts (paper_id, audio_path, duration_sec, created_at) VALUES (?, ?, ?, ?)",
        (paper_id, audio_path, duration_sec, now),
    )
    conn.commit()


def podcast_get(conn: sqlite3.Connection, paper_id: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM podcasts WHERE paper_id=?", (paper_id,)).fetchone()


# ---------- Settings ----------
def setting_get(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row[0] if row else None


def setting_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()


# ---------- Collect logs ----------
def collect_log_insert(conn: sqlite3.Connection, run_at: str, new_count: int) -> None:
    now = _now()
    conn.execute("INSERT INTO collect_logs (run_at, new_count, created_at) VALUES (?, ?, ?)", (run_at, new_count, now))
    conn.commit()
