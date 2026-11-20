import os
import time
import uuid
import redis
from fastapi import FastAPI, Request, HTTPException

app = FastAPI(title="Rate Limiter")

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)

LIMIT = 5            # max requests
WINDOW_MS = 60_000   # per 60 seconds

# Lua script runs atomically inside Redis (no race conditions)
SLIDING_WINDOW = r.register_script("""
local key    = KEYS[1]
local now    = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit  = tonumber(ARGV[3])
local member = ARGV[4]

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local count = redis.call('ZCARD', key)

if count < limit then
  redis.call('ZADD', key, now, member)
  redis.call('PEXPIRE', key, window)
  return {1, limit - count - 1, 0}
else
  local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
  local retry = window - (now - tonumber(oldest[2]))
  return {0, 0, retry}
end
""")

def rate_limit(request: Request):
    client_id = request.headers.get("X-API-Key") or request.client.host
    key = f"ratelimit:{client_id}"
    now = int(time.time() * 1000)
    allowed, remaining, retry_ms = SLIDING_WINDOW(
        keys=[key], args=[now, WINDOW_MS, LIMIT, f"{now}-{uuid.uuid4()}"]
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Try again later.",
            headers={"Retry-After": str(int(retry_ms / 1000) + 1)},
        )
    return remaining

@app.get("/")
def home():
    return {"message": "Rate limiter is running. Try /api/data"}

@app.get("/api/data")
def get_data(request: Request):
    remaining = rate_limit(request)
    return {"message": "Request allowed", "remaining": remaining}