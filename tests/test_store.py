import importlib
from pathlib import Path

import store


def test_import_does_not_create_db_in_cwd(tmp_path: Path, monkeypatch):
    """다른 CWD에서 store를 import해도 현재 디렉터리에 dealgom.db를 만들지 않는다."""
    store.close_db()
    monkeypatch.delenv("DEALGOM_DB_PATH", raising=False)
    monkeypatch.chdir(tmp_path)

    importlib.reload(store)

    assert not (tmp_path / "dealgom.db").exists()
    assert store.DEFAULT_DB_PATH == Path(store.__file__).resolve().parent / "dealgom.db"


def test_is_new_and_mark_seen_isolated_db(isolated_db: Path):
    assert store.is_new("hotgusa", "item-1") is True

    store.mark_seen("hotgusa", "item-1", 19900)
    assert store.is_new("hotgusa", "item-1") is False

    # 같은 item_id라도 source가 다르면 신규로 취급
    assert store.is_new("other", "item-1") is True

    # 중복 mark_seen 호출 시 에러 없이 무시
    store.mark_seen("hotgusa", "item-1", 18000)
    assert store.is_new("hotgusa", "item-1") is False
