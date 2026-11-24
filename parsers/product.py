import json
import re

from bs4 import BeautifulSoup

PRICE_RE = re.compile(r"([\d,]+)\s*원")


def _og(soup: BeautifulSoup, prop: str) -> str | None:
    tag = soup.find("meta", attrs={"property": prop})
    return tag.get("content") if tag else None


def _ld_product(soup: BeautifulSoup) -> dict | None:
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads((tag.string or tag.get_text()).strip())
        except json.JSONDecodeError:
            continue
        for node in data if isinstance(data, list) else [data]:
            if isinstance(node, dict) and node.get("@type") == "Product":
                return node
    return None


def _to_int(value) -> int | None:
    digits = re.sub(r"[^\d]", "", str(value)) if value is not None else ""
    return int(digits) if digits else None


def parse_product(html: str) -> dict | None:
    soup = BeautifulSoup(html, "lxml")
    ld = _ld_product(soup) or {}
    offers = ld.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}

    title = ld.get("name") or _og(soup, "og:title") or (
        soup.title.string.strip() if soup.title and soup.title.string else None
    )
    url = offers.get("url") or _og(soup, "og:url")
    if not title or not url:
        return None

    price = _to_int(offers.get("price"))
    if price is None:                      # ld+json에 없으면 og:description에서 보조 추출
        m = PRICE_RE.search(_og(soup, "og:description") or "")
        price = _to_int(m.group(1)) if m else None

    avail = str(offers.get("availability") or "")
    in_stock = True if avail.endswith("InStock") else False if avail.endswith("OutOfStock") else None

    return {
        "item_id": url.rstrip("/").rsplit("/product/", 1)[-1],
        "title": title.strip(),
        "price": price,
        "in_stock": in_stock,
        "shipping": None,
        "url": url,
        "market": None,
        "community": None,
    }
