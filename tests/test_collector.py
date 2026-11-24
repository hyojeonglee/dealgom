import httpx
import pytest

import agents.collector_hotgusa as collector
from schemas import RawDeal
from tests.test_parsers import SYNTHETIC_PRODUCT_HTML, SYNTHETIC_SEARCH_HTML


def _make_search_html(count: int) -> str:
    elements = ",\n".join(
        f'{{"url": "https://www.hotgusa.com/product/7_{i}", "name": "기저귀 딜 {i}"}}'
        for i in range(1, count + 1)
    )
    return f"""
    <html><head>
    <script type="application/ld+json">
    {{"@type": "ItemList", "itemListElement": [{elements}]}}
    </script>
    </head></html>
    """


def test_collector_sample_mode_and_dedup(isolated_db, tmp_path, monkeypatch):
    sample_file = tmp_path / "search.html"
    sample_file.write_text(SYNTHETIC_SEARCH_HTML, encoding="utf-8")

    published: list[tuple[str, RawDeal]] = []
    monkeypatch.setattr(collector, "LIVE", False)
    monkeypatch.setattr(collector, "SAMPLE_SEARCH", sample_file)
    monkeypatch.setattr(collector, "publish", lambda topic, msg: published.append((topic, msg)) or "0-0")

    # 1회차: 2건 발행 (키워드가 여러 개여도 후보 중복 제거됨)
    collector.run_once()
    assert len(published) == 2
    assert all(topic == "deal.raw" and isinstance(deal, RawDeal) for topic, deal in published)
    assert all(deal.price is None for _, deal in published)

    # 2회차: 이미 seen 처리되어 추가 발행 0건
    collector.run_once()
    assert len(published) == 2


def test_collector_live_mode_fetches_product_and_defers_excess(isolated_db, monkeypatch):
    search_html = _make_search_html(5)
    published: list[tuple[str, RawDeal]] = []

    monkeypatch.setattr(collector, "LIVE", True)
    monkeypatch.setattr(collector, "REQUEST_GAP", 0)
    monkeypatch.setattr(collector, "MAX_PRODUCT_FETCH", 2)
    monkeypatch.setattr(collector, "fetch_search", lambda kw: search_html)
    monkeypatch.setattr(collector, "fetch_product", lambda url: SYNTHETIC_PRODUCT_HTML)
    monkeypatch.setattr(collector, "publish", lambda topic, msg: published.append((topic, msg)) or "0-0")

    # 1회차: 상한 2건 발행, 3건 이월
    collector.run_once()
    assert len(published) == 2
    assert all(deal.price == 39900 and deal.in_stock is True for _, deal in published)

    # 2회차: 이월된 3건 중 2건 발행, 1건 이월
    collector.run_once()
    assert len(published) == 4

    # 3회차: 마지막 1건 발행
    collector.run_once()
    assert len(published) == 5

    # 4회차: 모두 처리되어 추가 발행 0건
    collector.run_once()
    assert len(published) == 5


@pytest.mark.parametrize("status_code", [403, 429])
def test_collector_stops_immediately_on_block_signal(isolated_db, monkeypatch, status_code: int):
    req = httpx.Request("GET", "https://www.hotgusa.com/search/test")
    resp = httpx.Response(status_code, request=req)
    err = httpx.HTTPStatusError("Blocked", request=req, response=resp)

    calls = 0

    def _fail_search(kw: str) -> str:
        nonlocal calls
        calls += 1
        raise err

    published: list = []
    monkeypatch.setattr(collector, "LIVE", True)
    monkeypatch.setattr(collector, "REQUEST_GAP", 0)
    monkeypatch.setattr(collector, "fetch_search", _fail_search)
    monkeypatch.setattr(collector, "publish", lambda topic, msg: published.append((topic, msg)) or "0-0")

    collector.run_once()
    assert calls == 1
    assert len(published) == 0
