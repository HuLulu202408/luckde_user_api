
import os

import redis
from dotenv import load_dotenv

load_dotenv()

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "127.0.0.1"),
    port=int(os.getenv("REDIS_PORT", "6380")),
    db=int(os.getenv("REDIS_DB", "0")),
    password=os.getenv("REDIS_PASSWORD") or None,
    decode_responses=True,
    socket_connect_timeout=3,
    socket_timeout=3,
)


def check_redis():
    return redis_client.ping()
