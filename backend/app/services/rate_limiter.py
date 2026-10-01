from __future__ import annotations

import logging
import time

import redis

from app.config import Config

logger: logging.Logger = logging.getLogger(__name__)

# Initialize connection pool for Valkey (Redis-compatible)
try:
	valkey_pool: redis.ConnectionPool = redis.ConnectionPool.from_url(
		Config.RATE_LIMIT_STORAGE_URL, decode_responses=True
	)
	valkey_client: redis.Redis = redis.Redis(connection_pool=valkey_pool)
except Exception as e:
	logger.warning("Could not establish Valkey pool for rate limiting: %s", str(e))
	valkey_client = None  # type: ignore[assignment]


def is_rate_limited(key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
	"""
	Check rate limit using Valkey sliding window algorithm.
	Returns: (is_limited: bool, remaining_requests: int)
	"""
	if valkey_client is None:
		# Fail open if Valkey is unreachable in local dev
		return False, limit

	now: float = time.time()
	window_start: float = now - window_seconds
	full_key: str = f"ratelimit:{key}"

	try:
		pipe: redis.client.Pipeline = valkey_client.pipeline(transaction=True)
		# 1. Remove expired hits outside the current sliding window
		pipe.zremrangebyscore(full_key, 0, window_start)
		# 2. Get current hit count in window
		pipe.zcard(full_key)
		# 3. Add current timestamp
		pipe.zadd(full_key, {f"{now}": now})
		# 4. Set TTL on the key to automatically clean up
		pipe.expire(full_key, window_seconds + 5)

		results: list[int] = pipe.execute()
		current_count: int = results[1]

		if current_count >= limit:
			# Over limit, remove the timestamp we just added to keep window clean
			valkey_client.zrem(full_key, f"{now}")
			return True, 0

		remaining: int = max(0, limit - (current_count + 1))
		return False, remaining

	except Exception as exc:
		logger.error("Valkey rate limiting check failed: %s. Failing open.", str(exc))
		return False, limit
