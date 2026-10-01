from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from flask import Response, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from app.models.enums import UserRole
from app.services.rate_limiter import is_rate_limited

F = TypeVar("F", bound=Callable[..., Any])


def api_success(
	data: Any = None, message: str | None = None, status_code: int = 200
) -> tuple[Response, int]:
	"""Standardized success JSON response envelope."""
	payload: dict[str, Any] = {"success": True}
	if message is not None:
		payload["message"] = message
	if data is not None:
		payload["data"] = data
	return jsonify(payload), status_code


def api_error(
	code: str, message: str, details: Any = None, status_code: int = 400
) -> tuple[Response, int]:
	"""Standardized error JSON response envelope."""
	payload: dict[str, Any] = {
		"success": False,
		"error": {
			"code": code,
			"message": message,
			"details": details or {},
		},
	}
	return jsonify(payload), status_code


def require_roles(*allowed_roles: UserRole) -> Callable[[F], F]:
	"""Decorator enforcing JWT authentication and role membership."""

	def decorator(fn: F) -> F:
		@wraps(fn)
		def wrapper(*args: Any, **kwargs: Any) -> Any:
			verify_jwt_in_request()
			claims: dict[str, Any] = get_jwt()
			user_role: str = str(claims.get("role", ""))
			allowed_values: set[str] = {r.value for r in allowed_roles}

			if user_role not in allowed_values:
				return api_error(
					code="FORBIDDEN_ROLE",
					message=f"Access denied. Requires one of roles: {', '.join(allowed_values)}",
					status_code=403,
				)
			return fn(*args, **kwargs)

		return wrapper  # type: ignore[return-value]

	return decorator


def rate_limit(limit: int, window_seconds: int, key_prefix: str = "endpoint") -> Callable[[F], F]:
	"""
	Synchronous backend rate limiting decorator using Valkey sliding window.
	Identifies user by JWT identity or client IP.
	"""

	def decorator(fn: F) -> F:
		@wraps(fn)
		def wrapper(*args: Any, **kwargs: Any) -> Any:
			try:
				verify_jwt_in_request(optional=True)
				identity = get_jwt_identity()
				client_identifier: str = (
					f"user:{identity}" if identity else f"ip:{request.remote_addr}"
				)
			except Exception:
				client_identifier = f"ip:{request.remote_addr}"

			rate_key: str = f"{key_prefix}:{client_identifier}"
			limited, _remaining = is_rate_limited(
				rate_key, limit=limit, window_seconds=window_seconds
			)

			if limited:
				return api_error(
					code="RATE_LIMIT_EXCEEDED",
					message=f"Too many requests. Limit is {limit} per {window_seconds}s. Please wait.",
					status_code=429,
				)

			return fn(*args, **kwargs)

		return wrapper  # type: ignore[return-value]

	return decorator
