import json
from pathlib import Path

from bs4 import BeautifulSoup

soup = BeautifulSoup(Path("samples/search_sample.html").read_text(encoding="utf-8"), "lxml")
main = soup.find("main")
anchors = main.select('a[href^="/product/"]') if main else []
print("main 안의 상품 링크 수:", len(anchors))

if anchors:
    node = anchors[0]
    for _ in range(6):
        parent = node.parent
        if parent is None:
            break
        if len({a["href"] for a in parent.select('a[href^="/product/"]')}) > 1:
            break
        node = parent
    for t in node.find_all("svg"):
        t.decompose()
    print("\n--- 첫 카드 HTML ---")
    print(str(node)[:3500])

print("\n--- ld+json ---")
for t in soup.find_all("script", type="application/ld+json"):
    raw = (t.string or t.get_text()).strip()
    try:
        data = json.loads(raw)
        print(json.dumps(data, ensure_ascii=False)[:2500])
    except Exception:
        print(raw[:2500])

