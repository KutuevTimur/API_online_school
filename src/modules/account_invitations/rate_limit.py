import hashlib
import time
from fastapi import Request, HTTPException


async def check_rate_limit(request: Request, action: str, identifier: str) -> None:
    """DB-backed fixed windows shared across workers; never trust forwarded IP headers."""
    config = request.app.state.config
    window = int(time.time()) // 900
    ip = request.client.host if request.client else "unknown"
    exceeded = False
    # Independent transaction persists failed attempts even when scenario rolls back.
    async with config.db_connection.session_local() as session:
        from src.modules.account_invitations.repository import RateLimitRepository
        repo = RateLimitRepository(session)
        await repo.cleanup(window)
        for dimension, value, limit in (("ip", ip, 100), ("account", identifier, 10)):
            key = hashlib.sha256(f"{action}:{dimension}:{value}".encode()).hexdigest()
            exceeded |= await repo.increment(key, window) > limit
        await session.commit()
    if exceeded:
        raise HTTPException(status_code=429, detail="Too many attempts", headers={"Retry-After": str(900 - int(time.time()) % 900)})
