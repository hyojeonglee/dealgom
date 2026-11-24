from uuid import uuid4

import pytest
import redis

import agents.collector_hotgusa as collector
import bus
from schemas import RawDeal
from tests.test_parsers import SYNTHETIC_SEARCH_HTML


def _redis_available() -> bool:
    try:
        return bool(bus.r.ping())
    except (redis.RedisError, OSError):
        return False


def test_redis_client_disables_socket_read_timeout():
    """xreadgroup(block=5000) 대기 중 redis-py 8.x 기본 5초 소켓 타임아웃에 걸리지 않아야 한다."""
    conn = bus.r.connection_pool.make_connection()
    assert conn.socket_timeout is None
    assert conn.socket_connect_timeout == 5


def test_collector_to_redis_stream_roundtrip(isolated_db, tmp_path, monkeypatch):
    if not _redis_available():
        pytest.skip("로컬 Redis 서버에 연결할 수 없어 Redis E2E 테스트를 건너뜁니다")

    sample_file = tmp_path / "search.html"
    sample_file.write_text(SYNTHETIC_SEARCH_HTML, encoding="utf-8")

    test_topic = f"deal.raw.pytest.{uuid4().hex[:8]}"
    test_group = "pytest-echo"

    monkeypatch.setattr(collector, "LIVE", False)
    monkeypatch.setattr(collector, "SAMPLE_SEARCH", sample_file)
    monkeypatch.setattr(collector, "publish", lambda _topic, msg: bus.publish(test_topic, msg))

    try:
        collector.run_once()
        assert bus.r.xlen(test_topic) == 2

        received: list[RawDeal] = []
        for _entry_id, deal in bus.subscribe(
            test_topic,
            group=test_group,
            consumer="pytest-1",
            model=RawDeal,
            block_ms=200,
        ):
            received.append(deal)
            if len(received) == 2:
                break

        assert len(received) == 2
        assert {d.source_item_id for d in received} == {"7_1001", "0_2002"}
    finally:
        bus.r.delete(test_topic)
