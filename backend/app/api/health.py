from __future__ import annotations

from typing import Any

from flask import Blueprint, Response
from sqlalchemy import text

from app.api.utils import api_success
from app.database import get_db_session
from app.services.rate_limiter import valkey_client

health_bp: Blueprint = Blueprint("health", __name__, url_prefix="/api/v1")


@health_bp.route("/health", methods=["GET"])
def health_check() -> tuple[Response, int]:
	"""Health check endpoint for Docker and edge proxy monitoring."""
	db_ok: bool = False
	valkey_ok: bool = False

	try:
		with get_db_session() as session:
			session.execute(text("SELECT 1"))
			db_ok = True
	except Exception:
		db_ok = False

	try:
		if valkey_client and valkey_client.ping():
			valkey_ok = True
	except Exception:
		valkey_ok = False

	status_data: dict[str, Any] = {
		"status": "healthy" if db_ok else "degraded",
		"database": "connected" if db_ok else "unreachable",
		"valkey": "connected" if valkey_ok else "unreachable",
	}
	return api_success(status_data)
