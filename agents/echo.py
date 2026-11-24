from bus import subscribe
from schemas import RawDeal

print("echo 시작, deal.raw 대기 중...", flush=True)
for entry_id, deal in subscribe("deal.raw", group="echo", consumer="echo-1", model=RawDeal):
    print(f"수신: {deal.title} | trace={deal.trace_id[:8]}", flush=True)

