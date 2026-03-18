import time
from collections import deque, defaultdict
from fastapi import Request, HTTPException, status

# In-memory store: IP -> path -> deque of timestamps
_rate_limit_store = defaultdict(lambda: defaultdict(deque))

async def check_rate_limit(request: Request, limit_count: int, window_seconds: int):
    """
    Simple in-memory sliding window rate limiter.
    Raises 429 if limit exceeded.
    Fail-open if client IP is unknown.
    """
    client_ip = request.client.host if request.client else None
    
    if not client_ip:
        # Fail open
        return

    path = request.url.path
    now = time.time()
    
    # Get timestamps for this IP and path
    timestamps = _rate_limit_store[client_ip][path]
    
    # Remove old timestamps
    while timestamps and timestamps[0] < now - window_seconds:
        timestamps.popleft()
    
    # Check limit
    if len(timestamps) >= limit_count:
        retry_after = int(window_seconds - (now - timestamps[0])) if timestamps else window_seconds
        
        # Contract: {"detail":"Too many requests","code":"RATE_LIMITED","context":{"retry_after": <seconds>}}
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "detail": "Too many requests",
                "code": "RATE_LIMITED",
                "context": {"retry_after": retry_after}
            },
            headers={"Retry-After": str(retry_after)}
        )
    
    # Add new timestamp
    timestamps.append(now)

# Partial functions or dependencies can be created for specific limits
async def rate_limit_detect(request: Request):
    await check_rate_limit(request, limit_count=5, window_seconds=10)

async def rate_limit_feedback(request: Request):
    await check_rate_limit(request, limit_count=20, window_seconds=60)

async def rate_limit_upload(request: Request):
    await check_rate_limit(request, limit_count=2, window_seconds=60)
