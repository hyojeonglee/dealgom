import random
import time
from pathlib import Path
from urllib.parse import quote

import httpx

from bus import publish
from parsers.product import parse_product
from parsers.search import parse_search
from schemas import RawDeal
from store import is_new, mark_seen

SOURCE = "hotgusa"
LIVE = False                       # False: samples/ 파일만 읽음 (서버 요청 없음) / True: 실제 요청
SEARCH_KEYWORDS = ["기저귀", "하기스", "팸퍼스", "물티슈", "아기", "유아"]
SEARCH_BASE = "https://www.hotgusa.com/search/"
HEADERS = {"User-Agent": "dealgom-research-bot"}
REQUEST_GAP = 10                   # 요청 사이 간격(초)
INTERVAL = 7200                    # 한 주기 간격: 2시간
MAX_PRODUCT_FETCH = 10             # 한 주기에 받을 상품 페이지 상한
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_SEARCH = PROJECT_ROOT / "samples/search_sample.html"


def _get(url: str) -> str:
    resp = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
    resp.raise_for_status()
    return resp.text


def fetch_search(keyword: str) -> str:
    if not LIVE:
        return SAMPLE_SEARCH.read_text(encoding="utf-8")
    return _get(SEARCH_BASE + quote(keyword))


def fetch_product(url: str) -> str | None:
    if not LIVE:
        return None                # 샘플 모드에서는 상품 페이지를 받지 않음 (가격은 None)
    return _get(url)


def _blocked(e: Exception) -> bool:
    return isinstance(e, httpx.HTTPStatusError) and e.response.status_code in (403, 429)


def run_once() -> None:
    # 1) 키워드별 검색 페이지 → 새 딜 후보 (키워드 간 중복 제거)
    candidates: dict[str, dict] = {}
    for kw in SEARCH_KEYWORDS:
        try:
            items = parse_search(fetch_search(kw))
        except Exception as e:
            print(f"[{kw}] 검색 페이지 실패: {e}", flush=True)
            if _blocked(e):
                print("차단/제한 신호 감지: 이번 주기 중단", flush=True)
                return
            continue
        if not items:
            print(f"[{kw}] 경고: 파싱 0건, 사이트 구조가 바뀌었을 수 있음", flush=True)
        for it in items:
            if it["item_id"] not in candidates and is_new(SOURCE, it["item_id"]):
                candidates[it["item_id"]] = it
        if LIVE:
            time.sleep(REQUEST_GAP)

    # 2) 새 딜의 상품 페이지에서 가격/전체 제목 → 발행
    fetched = sent = deferred = 0
    for it in candidates.values():
        title, price, in_stock = it["title"], None, None
        if LIVE:
            if fetched >= MAX_PRODUCT_FETCH:
                deferred += 1      # seen에 기록하지 않아서 다음 주기에 다시 후보가 됨
                continue
            try:
                html = fetch_product(it["url"])
            except Exception as e:
                print(f"상품 페이지 실패 {it['item_id']}: {e}", flush=True)
                if _blocked(e):
                    print("차단/제한 신호 감지: 이번 주기 중단", flush=True)
                    break
                continue           # seen 기록 안 함: 다음 주기에 재시도
            fetched += 1
            time.sleep(REQUEST_GAP)
            parsed = parse_product(html) if html else None
            if parsed:
                title, price, in_stock = parsed["title"], parsed["price"], parsed["in_stock"]

        deal = RawDeal(
            source=SOURCE,
            source_item_id=it["item_id"],
            title=title,
            price=price,
            url=it["url"],
            in_stock=in_stock,
        )
        publish("deal.raw", deal)
        mark_seen(SOURCE, it["item_id"], price)
        sent += 1

    print(
        f"후보 {len(candidates)} | 상품 페이지 {fetched} | 발행 {sent} | 다음 주기로 이월 {deferred}",
        flush=True,
    )


if __name__ == "__main__":
    print(f"collector 시작 (LIVE={LIVE})", flush=True)
    while True:
        try:
            run_once()
        except Exception as e:     # 한 번 실패해도 프로세스는 살려둠
            print(f"수집 실패: {e}", flush=True)
        time.sleep(INTERVAL + random.randint(0, 300))
