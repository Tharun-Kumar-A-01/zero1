from __future__ import annotations

import logging
from typing import Any

from flask import Flask, Response
from flask_jwt_extended import JWTManager
from sqlalchemy import select

from app.api.admin import admin_bp
from app.api.auth import auth_bp
from app.api.health import health_bp
from app.api.mentor import mentor_bp
from app.api.student import student_bp
from app.api.utils import api_error
from app.config import Config
from app.database import get_db_session, init_db
from app.models.enums import UserRole
from app.models.user import User

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger: logging.Logger = logging.getLogger(__name__)


def seed_initial_admin() -> None:
	"""Seed super administrator account from Config if no admin exists."""
	try:
		with get_db_session() as session:
			stmt = select(User).where(User.role == UserRole.ADMIN)
			existing_admin: User | None = session.scalars(stmt).first()
			if existing_admin is None:
				logger.info(
					"No admin user found. Creating initial admin from environment: %s",
					Config.INITIAL_ADMIN_EMAIL,
				)
				admin = User(
					name=Config.INITIAL_ADMIN_NAME,
					email=Config.INITIAL_ADMIN_EMAIL,
					role=UserRole.ADMIN,
					is_active=True,
				)
				admin.set_password(Config.INITIAL_ADMIN_PASSWORD)
				session.add(admin)
	except Exception as e:
		logger.warning("Could not auto-seed admin (database may be uninitialized yet): %s", str(e))


def create_app() -> Flask:
	"""Application factory pattern configuring Flask app."""
	app: Flask = Flask(__name__)
	app.config.from_object(Config)

	# Initialize JWT
	jwt: JWTManager = JWTManager(app)

	@jwt.unauthorized_loader
	def custom_unauthorized_response(err: str) -> tuple[Response, int]:
		return api_error(
			"UNAUTHORIZED", f"Missing or invalid authentication token: {err}", status_code=401
		)

	@jwt.expired_token_loader
	def custom_expired_token_response(
		jwt_header: dict[str, Any], jwt_payload: dict[str, Any]
	) -> tuple[Response, int]:
		return api_error(
			"TOKEN_EXPIRED", "The token has expired. Please refresh your session.", status_code=401
		)

	@jwt.invalid_token_loader
	def custom_invalid_token_response(err: str) -> tuple[Response, int]:
		return api_error("INVALID_TOKEN", f"Invalid token: {err}", status_code=401)

	# Global Standardized Error Handlers
	@app.errorhandler(400)
	def handle_bad_request(e: Any) -> tuple[Response, int]:
		return api_error(
			"BAD_REQUEST", str(getattr(e, "description", "Bad Request")), status_code=400
		)

	@app.errorhandler(404)
	def handle_not_found(e: Any) -> tuple[Response, int]:
		return api_error(
			"NOT_FOUND", "The requested endpoint or resource was not found.", status_code=404
		)

	@app.errorhandler(405)
	def handle_method_not_allowed(e: Any) -> tuple[Response, int]:
		return api_error(
			"METHOD_NOT_ALLOWED", "HTTP method not allowed for this route.", status_code=405
		)

	@app.errorhandler(500)
	def handle_server_error(e: Any) -> tuple[Response, int]:
		logger.error("Internal Server Error: %s", str(e))
		return api_error(
			"INTERNAL_SERVER_ERROR", "An unexpected server error occurred.", status_code=500
		)

	# Register Blueprints
	app.register_blueprint(health_bp)
	app.register_blueprint(auth_bp)
	app.register_blueprint(student_bp)
	app.register_blueprint(mentor_bp)
	app.register_blueprint(admin_bp)

	# Initialize tables and seed initial admin on app startup
	with app.app_context():
		try:
			init_db()
			seed_initial_admin()
		except Exception as e:
			logger.warning("Database init on startup deferred: %s", str(e))

	return app
