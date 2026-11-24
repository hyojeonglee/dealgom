from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

SCHEMA_VERSION = 1


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Envelope(BaseModel):
    """모든 메시지 공통 필드."""
    schema_version: int = SCHEMA_VERSION
    msg_id: str = Field(default_factory=lambda: uuid4().hex)
    trace_id: str = Field(default_factory=lambda: uuid4().hex)  # 한 딜의 전 구간 추적용
    created_at: datetime = Field(default_factory=_now)


class RawDeal(Envelope):
    """Collector가 발행하는 원본 딜 (deal.raw)."""
    source: str                    # "ppomppu", "clien", "coupang" ...
    source_item_id: str            # 소스 안에서의 글/상품 ID (중복 제거용)
    title: str
    body: str | None = None        # 게시글 본문 일부 (가격, 수량 파싱용)
    price: int | None = None       # 소스가 구조화해 주면 채우고, 아니면 Normalizer가 추출
    shipping: int | None = None
    url: str


class NormalizedDeal(Envelope):
    """Normalizer가 발행하는 정규화 딜 (deal.normalized). 지금은 쓰지 않고 자리만 잡아둠."""
    raw_msg_id: str
    brand: str | None = None
    stage: str | None = None
    min_kg: float | None = None
    max_kg: float | None = None
    total_count: int | None = None
    unit_price: float | None = None

