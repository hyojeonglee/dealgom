import os
from pathlib import Path

import redis
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv(Path(__file__).resolve().parent / ".env")

r = redis.Redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379"),
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=None,
)


def publish(topic: str, msg: BaseModel) -> str:
    """메시지를 토픽(스트림)에 발행. 스트림이 없으면 자동 생성."""
    return r.xadd(topic, {"data": msg.model_dump_json()}, maxlen=10000, approximate=True)


def subscribe(topic: str, group: str, consumer: str, model: type[BaseModel], block_ms: int = 5000):
    """토픽을 구독하며 (entry_id, 메시지) 를 하나씩 내보냄. 처리가 끝나야 ack."""
    try:
        r.xgroup_create(topic, group, id="0", mkstream=True)
    except redis.ResponseError as e:
        if "BUSYGROUP" not in str(e):   # 이미 그룹이 있으면 정상
            raise
    while True:
        resp = r.xreadgroup(group, consumer, {topic: ">"}, count=10, block=block_ms)
        for _, entries in resp or []:
            for entry_id, fields in entries:
                yield entry_id, model.model_validate_json(fields["data"])
                r.xack(topic, group, entry_id)   # for 루프 본문이 끝난 뒤에 실행됨

