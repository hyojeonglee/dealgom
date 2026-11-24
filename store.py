import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DB_PATH = PROJECT_ROOT / "dealgom.db"

_conn: sqlite3.Connection | None = None
_conn_path: str | None = None


def _resolve_db_path(db_path: str | Path | None = None) -> str:
    if db_path is not None:
        return str(db_path)
    env_path = os.getenv("DEALGOM_DB_PATH")
    if env_path:
        return env_path
    return str(DEFAULT_DB_PATH)


def init_db(db_path: str | Path | None = None) -> sqlite3.Connection:
    """SQLite 연결을 초기화하고 seen 테이블을 준비한다."""
    global _conn, _conn_path
    target = _resolve_db_path(db_path)
    if _conn is not None:
        _conn.close()
    _conn = sqlite3.connect(target)
    _conn_path = target
    _conn.execute(
        """CREATE TABLE IF NOT EXISTS seen (
            source TEXT, item_id TEXT, price INTEGER, first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (source, item_id)
        )"""
    )
    _conn.commit()
    return _conn


def close_db() -> None:
    """열려 있는 SQLite 연결을 닫는다."""
    global _conn, _conn_path
    if _conn is not None:
        _conn.close()
        _conn = None
        _conn_path = None


def _get_conn() -> sqlite3.Connection:
    target = _resolve_db_path()
    if _conn is None or _conn_path != target:
        return init_db(target)
    return _conn


def is_new(source: str, item_id: str) -> bool:
    row = _get_conn().execute(
        "SELECT 1 FROM seen WHERE source=? AND item_id=?",
        (source, item_id),
    ).fetchone()
    return row is None


def mark_seen(source: str, item_id: str, price: int | None) -> None:
    conn = _get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO seen (source, item_id, price) VALUES (?,?,?)",
        (source, item_id, price),
    )
    conn.commit()
