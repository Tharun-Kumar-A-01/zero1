from __future__ import annotations

import io
from typing import Any

from flask.testing import FlaskClient

from app.models.user import User


def test_login_success(client: FlaskClient, test_student_user: User) -> None:
	res = client.post(
		"/api/auth/login", json={"email": test_student_user.email, "password": "StudentPass@123"}
	)
	assert res.status_code == 200
	data: dict[str, Any] = res.get_json()
	assert data["success"] is True
	assert "access_token" in data["data"]
	assert "refresh_token" in data["data"]
	assert data["data"]["user"]["email"] == test_student_user.email


def test_login_wrong_password(client: FlaskClient, test_student_user: User) -> None:
	res = client.post(
		"/api/auth/login", json={"email": test_student_user.email, "password": "WrongPassword!"}
	)
	assert res.status_code == 401
	data: dict[str, Any] = res.get_json()
	assert data["success"] is False
	assert data["error"]["code"] == "INVALID_CREDENTIALS"


def test_refresh_token(client: FlaskClient, test_student_user: User) -> None:
	login_res = client.post(
		"/api/auth/login", json={"email": test_student_user.email, "password": "StudentPass@123"}
	)
	refresh_token: str = login_res.get_json()["data"]["refresh_token"]

	refresh_res = client.post(
		"/api/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"}
	)
	assert refresh_res.status_code == 200
	data: dict[str, Any] = refresh_res.get_json()
	assert data["success"] is True
	assert "access_token" in data["data"]


def test_role_authorization_guard(
	client: FlaskClient, student_auth_headers: dict[str, str], admin_auth_headers: dict[str, str]
) -> None:
	# Student attempting to access Admin endpoint -> 403 Forbidden
	forbidden_res = client.get("/api/admin/users", headers=student_auth_headers)
	assert forbidden_res.status_code == 403
	assert forbidden_res.get_json()["error"]["code"] == "FORBIDDEN_ROLE"

	# Admin accessing Admin endpoint -> 200 OK
	allowed_res = client.get("/api/admin/users", headers=admin_auth_headers)
	assert allowed_res.status_code == 200


def test_admin_mentor_rotation_endpoints(
	client: FlaskClient, admin_auth_headers: dict[str, str], test_admin_user: User
) -> None:
	# Test POST /api/admin/mentors/rotation
	payload = {
		"user_id": test_admin_user.id,
		"week_start_date": "2026-11-02",
		"week_end_date": "2026-11-08",
	}
	post_res = client.post("/api/admin/mentors/rotation", json=payload, headers=admin_auth_headers)
	assert post_res.status_code == 200
	post_data: dict[str, Any] = post_res.get_json()
	assert post_data["success"] is True
	assert post_data["data"]["user_id"] == test_admin_user.id

	# Test GET /api/admin/mentors/rotation
	get_res = client.get("/api/admin/mentors/rotation", headers=admin_auth_headers)
	assert get_res.status_code == 200
	get_data: dict[str, Any] = get_res.get_json()
	assert get_data["success"] is True
	assert len(get_data["data"]) >= 1


def test_admin_update_user(
	client: FlaskClient, admin_auth_headers: dict[str, str], test_student_user: User
) -> None:
	update_payload = {
		"name": "Updated Student Name",
		"email": "updated.student@dept.edu",
		"role": "mentor",
		"password": "NewStudentPassword@123",
	}
	res = client.put(
		f"/api/admin/users/{test_student_user.id}",
		json=update_payload,
		headers=admin_auth_headers,
	)
	assert res.status_code == 200
	data: dict[str, Any] = res.get_json()
	assert data["success"] is True
	assert data["data"]["name"] == "Updated Student Name"
	assert data["data"]["email"] == "updated.student@dept.edu"
	assert data["data"]["role"] == "mentor"


def test_student_assigned_as_mentor(
	client: FlaskClient, admin_auth_headers: dict[str, str], test_student_user: User
) -> None:
	payload = {
		"user_id": test_student_user.id,
		"week_start_date": "2026-12-07",
		"week_end_date": "2026-12-13",
	}
	res = client.post("/api/admin/mentors/rotation", json=payload, headers=admin_auth_headers)
	assert res.status_code == 200
	data: dict[str, Any] = res.get_json()
	assert data["success"] is True
	assert data["data"]["user_id"] == test_student_user.id


def test_custom_leaves_crud(client: FlaskClient, admin_auth_headers: dict[str, str]) -> None:
	# Create
	payload = {
		"title": "Semester Holiday",
		"start_date": "2026-12-24",
		"end_date": "2026-12-31",
		"description": "Winter term break",
	}
	create_res = client.post("/api/admin/leaves", json=payload, headers=admin_auth_headers)
	assert create_res.status_code == 200
	create_data = create_res.get_json()
	assert create_data["success"] is True
	leave_id: int = create_data["data"]["id"]

	# List
	list_res = client.get("/api/admin/leaves", headers=admin_auth_headers)
	assert list_res.status_code == 200
	list_data = list_res.get_json()
	assert list_data["success"] is True
	assert any(item["id"] == leave_id for item in list_data["data"])

	# Delete
	del_res = client.delete(f"/api/admin/leaves/{leave_id}", headers=admin_auth_headers)
	assert del_res.status_code == 200
	assert del_res.get_json()["success"] is True


def test_student_roster_upload_and_commit(client: FlaskClient, admin_auth_headers: dict[str, str]) -> None:
	# 1. Upload roster CSV file
	csv_content = b"Name,Roll Number,Email\nAarav Sharma,22CS901,aarav.roster@dept.edu\nDiya Patel,22CS902,diya.roster@dept.edu\n"
	upload_res = client.post(
		"/api/admin/students/import-upload",
		data={"file": (io.BytesIO(csv_content), "roster.csv"), "year_batch": "2026"},
		headers=admin_auth_headers,
		content_type="multipart/form-data",
	)
	assert upload_res.status_code == 200
	upload_data = upload_res.get_json()
	assert upload_data["success"] is True
	job_id: int = upload_data["data"]["job_id"]

	# 2. Commit import without sending rows (backend loads from storage_path)
	commit_res = client.post(
		"/api/admin/students/import-commit",
		json={
			"job_id": job_id,
			"column_mapping": {"name": 0, "roll_number": 1, "email": 2},
		},
		headers=admin_auth_headers,
	)
	assert commit_res.status_code == 200
	commit_data = commit_res.get_json()
	assert commit_data["success"] is True
	assert commit_data["data"]["imported_count"] == 2
	assert commit_data["data"]["skipped_count"] == 0



