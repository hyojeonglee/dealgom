from pathlib import Path

from bs4 import BeautifulSoup

soup = BeautifulSoup(Path("samples/hotgusa_all.html").read_text(encoding="utf-8"), "lxml")
main = soup.find("main")
print("main 존재:", main is not None)
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
    print(str(node)[:4000])
