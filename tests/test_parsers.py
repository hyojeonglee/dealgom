import pytest

from parsers.product import parse_product
from parsers.search import parse_search
from tests.conftest import SAMPLES_DIR

SYNTHETIC_SEARCH_HTML = """
<html><head>
<script type="application/ld+json">
{
  "@type": "ItemList",
  "itemListElement": [
    {"url": "https://www.hotgusa.com/product/7_1001", "name": " 하기스 기저귀 4단계 6팩 "},
    {"url": "https://www.hotgusa.com/product/7_1001", "name": "중복 항목"},
    {"url": "https://www.hotgusa.com/category/all", "name": "상품 아님"},
    {"url": "https://www.hotgusa.com/product/0_2002", "name": "팸퍼스 팬티형 5단계 4팩"}
  ]
}
</script>
</head><body></body></html>
"""

SYNTHETIC_PRODUCT_HTML = """
<html><head>
<meta property="og:title" content="OG 제목" />
<meta property="og:url" content="https://www.hotgusa.com/product/7_1001" />
<meta property="og:description" content="핫딜 39,900원 무료배송" />
<script type="application/ld+json">
{
  "@type": "Product",
  "name": "하기스 네이처메이드 4단계 6팩",
  "offers": {
    "url": "https://www.hotgusa.com/product/7_1001",
    "price": "39900",
    "availability": "https://schema.org/InStock"
  }
}
</script>
</head><body></body></html>
"""


def test_parse_search_synthetic():
    items = parse_search(SYNTHETIC_SEARCH_HTML)
    assert len(items) == 2
    assert items[0] == {
        "item_id": "7_1001",
        "title": "하기스 기저귀 4단계 6팩",
        "url": "https://www.hotgusa.com/product/7_1001",
    }
    assert items[1]["item_id"] == "0_2002"


def test_parse_product_synthetic():
    parsed = parse_product(SYNTHETIC_PRODUCT_HTML)
    assert parsed is not None
    assert parsed["item_id"] == "7_1001"
    assert parsed["title"] == "하기스 네이처메이드 4단계 6팩"
    assert parsed["price"] == 39900
    assert parsed["in_stock"] is True
    assert parsed["url"] == "https://www.hotgusa.com/product/7_1001"


def test_parse_product_fallback_og_price_and_out_of_stock():
    html = """
    <html><head>
    <meta property="og:title" content="아기 물티슈 10팩" />
    <meta property="og:url" content="https://www.hotgusa.com/product/9_999" />
    <meta property="og:description" content="특가 12,500 원" />
    <script type="application/ld+json">
    {"@type": "Product", "offers": {"availability": "https://schema.org/OutOfStock"}}
    </script>
    </head></html>
    """
    parsed = parse_product(html)
    assert parsed is not None
    assert parsed["price"] == 12500
    assert parsed["in_stock"] is False


def test_parse_search_sample_file():
    sample = SAMPLES_DIR / "search_sample.html"
    if not sample.exists():
        pytest.skip("samples/search_sample.html 파일이 없음")
    items = parse_search(sample.read_text(encoding="utf-8"))
    assert len(items) > 0
    assert all(it["item_id"] and it["title"] and "/product/" in it["url"] for it in items)


def test_parse_product_sample_file():
    sample = SAMPLES_DIR / "product_sample.html"
    if not sample.exists():
        pytest.skip("samples/product_sample.html 파일이 없음")
    parsed = parse_product(sample.read_text(encoding="utf-8"))
    assert parsed is not None
    assert isinstance(parsed["price"], int)
    assert parsed["in_stock"] is True
