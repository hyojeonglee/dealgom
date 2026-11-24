import json

from bs4 import BeautifulSoup


def _walk(node):
    """JSON 안에서 ItemList 객체를 전부 찾는다."""
    if isinstance(node, dict):
        if node.get("@type") == "ItemList":
            yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def parse_search(html: str) -> list[dict]:
    """검색 페이지의 ld+json ItemList에서 (item_id, title, url)을 뽑는다. 최신순."""
    soup = BeautifulSoup(html, "lxml")
    out, seen = [], set()
    for tag in soup.find_all("script", type="application/ld+json"):
        raw = (tag.string or tag.get_text()).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for lst in _walk(data):
            for el in lst.get("itemListElement", []):
                url, name = el.get("url"), el.get("name")
                if not url or not name or "/product/" not in url:
                    continue
                item_id = url.rstrip("/").rsplit("/product/", 1)[1]
                if item_id in seen:
                    continue
                seen.add(item_id)
                out.append({"item_id": item_id, "title": name.strip(), "url": url})
    return out
