from pathlib import Path

import httpx
import pytest

import store

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = PROJECT_ROOT / "samples"


@pytest.fixture(autouse=True)
def block_outbound_http(monkeypatch: pytest.MonkeyPatch):
    """테스트 중 실제 외부 URL로 HTTP 요청이 나가지 않도록 원천 차단한다."""

    def _blocked(*args, **kwargs):
        raise RuntimeError(f"테스트 중 외부 HTTP 요청 차단됨: args={args}, kwargs={kwargs}")

    monkeypatch.setattr(httpx, "get", _blocked)
    monkeypatch.setattr(httpx.Client, "send", _blocked)


@pytest.fixture
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """실제 dealgom.db를 건드리지 않는 테스트 전용 임시 SQLite DB."""
    db_file = tmp_path / "test_dealgom.db"
    monkeypatch.setenv("DEALGOM_DB_PATH", str(db_file))
    store.init_db(db_file)
    try:
        yield db_file
    finally:
        store.close_db()
