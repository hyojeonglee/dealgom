import pytest

import agents.collector_hotgusa as collector
from parsers.product import parse_product
from schemas import RawDeal
from tests.conftest import SAMPLES_DIR


def test_sample_search_through_collector(isolated_db, monkeypatch):
    """samples/search_sample.html을 collector(LIVE=False)로 읽어 RawDeal 목록을 출력한다."""
    sample_file = SAMPLES_DIR / "search_sample.html"
    if not sample_file.exists():
        pytest.skip("samples/search_sample.html 파일이 없음")

    published: list[RawDeal] = []
    monkeypatch.setattr(collector, "LIVE", False)
    monkeypatch.setattr(collector, "SAMPLE_SEARCH", sample_file)
    monkeypatch.setattr(collector, "publish", lambda _topic, msg: published.append(msg) or "0-0")

    collector.run_once()
    assert len(published) > 0

    print(f"\n[샘플 검색 결과 -> RawDeal {len(published)}건]")
    for idx, deal in enumerate(published, 1):
        print(f"  {idx:2d}. [{deal.source_item_id}] {deal.title} | trace={deal.trace_id[:8]}")

    # 같은 샘플로 한 번 더 실행하면 중복 제거되어 추가 발행 0건
    before = len(published)
    collector.run_once()
    assert len(published) == before


def test_sample_product_preview():
    """samples/product_sample.html을 파싱해 상품 상세 필드를 출력한다."""
    sample_file = SAMPLES_DIR / "product_sample.html"
    if not sample_file.exists():
        pytest.skip("samples/product_sample.html 파일이 없음")

    parsed = parse_product(sample_file.read_text(encoding="utf-8"))
    assert parsed is not None

    print("\n[샘플 상품 페이지 파싱 결과]")
    print(
        f"  [{parsed['item_id']}] {parsed['title']} | "
        f"가격={parsed['price']}원 | 재고={parsed['in_stock']}"
    )
