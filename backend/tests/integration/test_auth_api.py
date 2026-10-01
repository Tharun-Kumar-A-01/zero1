from __future__ import annotations

from typing import Any

from flask.testing import FlaskClient

from app.models.user import User


def test_login_success(client: FlaskClient, test_student_user: User) -> None:
	res = client.post(
		"/api/v1/auth/login", json={"email": test_student_user.email, "password": "StudentPass@123"}
	)
	assert res.status_code == 200
	data: dict[str, Any] = res.get_json()
	assert data["success"] is True
	assert "access_token" in data["data"]
	assert "refresh_token" in data["data"]
	assert data["data"]["user"]["email"] == test_student_user.email


def test_login_wrong_password(client: FlaskClient, test_student_user: User) -> None:
	res = client.post(
		"/api/v1/auth/login", json={"email": test_student_user.email, "password": "WrongPassword!"}
	)
	assert res.status_code == 401
	data: dict[str, Any] = res.get_json()
	assert data["success"] is False
	assert data["error"]["code"] == "INVALID_CREDENTIALS"


def test_refresh_token(client: FlaskClient, test_student_user: User) -> None:
	login_res = client.post(
		"/api/v1/auth/login", json={"email": test_student_user.email, "password": "StudentPass@123"}
	)
	refresh_token: str = login_res.get_json()["data"]["refresh_token"]

	refresh_res = client.post(
		"/api/v1/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"}
	)
	assert refresh_res.status_code == 200
	data: dict[str, Any] = refresh_res.get_json()
	assert data["success"] is True
	assert "access_token" in data["data"]


def test_role_authorization_guard(
	client: FlaskClient, student_auth_headers: dict[str, str], admin_auth_headers: dict[str, str]
) -> None:
	# Student attempting to access Admin endpoint -> 403 Forbidden
	forbidden_res = client.get("/api/v1/admin/users", headers=student_auth_headers)
	assert forbidden_res.status_code == 403
	assert forbidden_res.get_json()["error"]["code"] == "FORBIDDEN_ROLE"

	# Admin accessing Admin endpoint -> 200 OK
	allowed_res = client.get("/api/v1/admin/users", headers=admin_auth_headers)
	assert allowed_res.status_code == 200
