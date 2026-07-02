import json
import os
from typing import Any, Dict, Optional

import redis


QUEUE_NAME = os.getenv("TRANSACTION_QUEUE", "transactions:incoming")
QUEUE_BACKEND = os.getenv("QUEUE_BACKEND", "redis")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_MEMORY_QUEUE = []


def get_backend_name() -> str:
    return QUEUE_BACKEND


def get_redis_client():
    return redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
    )


def enqueue_transaction(payload: Dict[str, Any]) -> int:
    encoded_payload = json.dumps(payload, default=str)

    if QUEUE_BACKEND == "memory":
        _MEMORY_QUEUE.insert(0, encoded_payload)
        return len(_MEMORY_QUEUE)

    client = get_redis_client()
    return client.lpush(QUEUE_NAME, encoded_payload)


def dequeue_transaction(timeout: int = 5) -> Optional[Dict[str, Any]]:
    if QUEUE_BACKEND == "memory":
        if not _MEMORY_QUEUE:
            return None

        encoded_payload = _MEMORY_QUEUE.pop()
        return json.loads(encoded_payload)

    client = get_redis_client()
    item = client.brpop(QUEUE_NAME, timeout=timeout)

    if item is None:
        return None

    _, encoded_payload = item
    return json.loads(encoded_payload)


def get_queue_depth() -> int:
    if QUEUE_BACKEND == "memory":
        return len(_MEMORY_QUEUE)

    client = get_redis_client()
    return client.llen(QUEUE_NAME)
