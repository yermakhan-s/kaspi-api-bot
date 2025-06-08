import time, redis
from .settings import settings

_r   = redis.from_url(settings.REDIS_URL)
KEY  = "kaspi_since_ts"
TTL  = 24*60*60  # сутки

def read_since_ts(default: int) -> int:
    val = _r.get(KEY)
    return int(val) if val else default

def write_since_ts(ts: int) -> None:
    _r.set(KEY, ts, ex=TTL)