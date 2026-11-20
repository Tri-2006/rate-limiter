# Rate Limiter (Redis + FastAPI)

Sliding window rate limiter: 5 requests per 60 seconds per client. It uses a Redis sorted set to store request timestamps.

## Run
1. Create a Redis database (for example a free one on upstash.com) and copy its connection URL.
2. pip install -r requirements.txt
3. Set the environment variable (PowerShell):
   $env:REDIS_URL = "your-redis-url"
4. uvicorn main:app --reload
5. In a second terminal: python test_limiter.py

Expected: requests 1-5 return 200, requests 6-8 return 429.