import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

LOC = re.compile(r"<loc>([^<]+)</loc>(?:<lastmod>([^<]+)</lastmod>)?")
BABY = ["기저귀", "하기스", "팸퍼스", "마미포코", "보솜이", "물티슈", "분유",
        "이유식", "젖병", "유아", "아기", "신생아", "베이비"]


def load(name: str):
    return LOC.findall(Path(f"samples/{name}").read_text(encoding="utf-8"))


prod = load("sitemap-product.xml")
dates = Counter(d for _, d in prod)
print("상품 URL:", len(prod))
for d, c in sorted(dates.items(), reverse=True)[:7]:
    print(" ", d, c)

for name, prefix in [("sitemap-search.xml", "/search/"), ("sitemap-trend.xml", "/price-trend/")]:
    items = load(name)
    hits = []
    for loc, d in items:
        if prefix not in loc:
            continue
        kw = unquote(loc.split(prefix, 1)[1])
        if any(b in kw for b in BABY):
            hits.append((kw, d, loc))
    print(f"\n{name}: 전체 {len(items)}, 육아 키워드 {len(hits)}")
    for kw, d, loc in hits[:30]:
        print(" ", kw, d, loc)
