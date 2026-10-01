from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager

from app.services.rate_limiter import valkey_client

logger: logging.Logger = logging.getLogger(__name__)


def acquire_distributed_lock(lock_name: str, timeout_seconds: int = 60) -> bool:
	"""
	Attempt to acquire a distributed lock using Valkey atomic SET NX EX.
	Returns True if lock acquired, False otherwise.
	"""
	if valkey_client is None:
		return True

	lock_key: str = f"lock:{lock_name}"
	try:
		res: bool | str | bytes | None = valkey_client.set(
			lock_key, "1", ex=timeout_seconds, nx=True
		)
		return bool(res)
	except Exception as e:
		logger.error("Error acquiring distributed lock %s: %s", lock_name, str(e))
		return False


def release_distributed_lock(lock_name: str) -> None:
	"""Release a previously acquired distributed lock."""
	if valkey_client is None:
		return

	lock_key: str = f"lock:{lock_name}"
	try:
		valkey_client.delete(lock_key)
	except Exception as e:
		logger.error("Error releasing distributed lock %s: %s", lock_name, str(e))


@contextmanager
def distributed_lock(lock_name: str, timeout_seconds: int = 60) -> Generator[bool, None, None]:
	"""Context manager for distributed locks."""
	acquired: bool = acquire_distributed_lock(lock_name, timeout_seconds)
	try:
		yield acquired
	finally:
		if acquired:
			release_distributed_lock(lock_name)
