import time

from bus import publish
from schemas import RawDeal

i = 0
while True:
    i += 1
    deal = RawDeal(
        source="dummy",
        source_item_id=str(i),
        title=f"[테스트] 기저귀 4단계 {i}번 딜",
        body="52매 3팩 / 39,000원 무료배송",
        url="https://example.com",
    )
    publish("deal.raw", deal)
    print(f"발행: {deal.title}", flush=True)
    time.sleep(2)

