from __future__ import annotations

from typing import Any

from flask import Blueprint, Response, request
from flask_jwt_extended import (
	create_access_token,
	create_refresh_token,
	get_jwt_identity,
	jwt_required,
)
from sqlalchemy import select

from app.api.utils import api_error, api_success, rate_limit
from app.database import get_db_session
from app.models.user import User
from app.services.sanitizer import sanitize_text
from app.services.streak_service import get_student_total_points

auth_bp: Blueprint = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth_bp.route("/login", methods=["POST"])
@rate_limit(limit=5, window_seconds=60, key_prefix="auth:login")
def login() -> tuple[Response, int]:
	"""Authenticate user and return JWT access/refresh tokens."""
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data:
		return api_error("INVALID_PAYLOAD", "Request body must be valid JSON.")

	email_raw: str = str(data.get("email", "")).strip().lower()
	password: str = str(data.get("password", ""))

	if not email_raw or not password:
		return api_error("MISSING_CREDENTIALS", "Email and password are required.")

	safe_email: str = sanitize_text(email_raw, max_length=255)

	with get_db_session() as session:
		stmt = select(User).where(User.email == safe_email)
		user: User | None = session.scalars(stmt).first()

		if user is None or not user.check_password(password):
			return api_error("INVALID_CREDENTIALS", "Invalid email or password.", status_code=401)

		if not user.is_active:
			return api_error(
				"ACCOUNT_INACTIVE",
				"Your account has been deactivated. Contact an administrator.",
				status_code=403,
			)

		claims: dict[str, Any] = {
			"role": user.role.value,
			"name": user.name,
			"email": user.email,
		}
		access_token: str = create_access_token(identity=str(user.id), additional_claims=claims)
		refresh_token: str = create_refresh_token(identity=str(user.id), additional_claims=claims)

		return api_success(
			{
				"access_token": access_token,
				"refresh_token": refresh_token,
				"user": user.to_dict(),
			},
			message="Login successful.",
		)


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
@rate_limit(limit=10, window_seconds=60, key_prefix="auth:refresh")
def refresh() -> tuple[Response, int]:
	"""Rotate access token using refresh token."""
	user_id: str = get_jwt_identity()
	with get_db_session() as session:
		user: User | None = session.get(User, int(user_id))
		if user is None or not user.is_active:
			return api_error("INVALID_USER", "User account not found or inactive.", status_code=401)

		claims: dict[str, Any] = {
			"role": user.role.value,
			"name": user.name,
			"email": user.email,
		}
		new_access_token: str = create_access_token(identity=str(user.id), additional_claims=claims)

		return api_success(
			{
				"access_token": new_access_token,
			},
			message="Access token refreshed.",
		)


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user() -> tuple[Response, int]:
	"""Retrieve current authenticated user profile and stats."""
	user_id: str = get_jwt_identity()
	with get_db_session() as session:
		user: User | None = session.get(User, int(user_id))
		if user is None:
			return api_error("USER_NOT_FOUND", "User not found.", status_code=404)

		user_data: dict[str, Any] = user.to_dict()
		if user.role.value == "student":
			user_data["total_points"] = get_student_total_points(session, user.id)
			user_data["current_streak"] = user.streak.current_streak if user.streak else 0
			user_data["longest_streak"] = user.streak.longest_streak if user.streak else 0

		return api_success(user_data)
