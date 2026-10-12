from __future__ import annotations

import json
from pathlib import Path

from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models.enums import UserRole
from app.models.user import User
from app.services.logger_service import (
	AI_AGENT_LOG_PATH,
	DATABASE_LOG_PATH,
	REQUESTS_LOG_PATH,
	log_ai_prompt,
	log_ai_response,
)


def test_incoming_request_logging_and_file_recording(client: FlaskClient) -> None:
	"""Verify that incoming requests log single-line console output and write to requests.log."""
	# Ensure log file exists or is created
	res = client.post(
		"/api/auth/login",
		json={"email": "nonexistent@dept.edu", "password": "SecretPassword123"},
	)
	assert res.status_code in (401, 404, 400)

	assert REQUESTS_LOG_PATH.exists()
	content = REQUESTS_LOG_PATH.read_text(encoding="utf-8")
	assert "/api/auth/login" in content
	assert "nonexistent@dept.edu" in content
	# Ensure password was masked!
	assert "SecretPassword123" not in content
	assert "***" in content


def test_database_write_logging(client: FlaskClient) -> None:
	"""Verify that database writes (INSERT, UPDATE, DELETE) are logged to database.log."""
	with get_db_session() as session:
		# 1. INSERT
		user = User(
			name="Logger Test Student",
			email="logger_test@dept.edu",
			role=UserRole.STUDENT,
			is_active=True,
		)
		user.set_password("StudentPassword123")
		session.add(user)
		session.flush()

		# 2. UPDATE
		user.name = "Logger Test Student Updated"
		session.flush()

		# 3. DELETE
		session.delete(user)
		session.flush()

	assert DATABASE_LOG_PATH.exists()
	db_content = DATABASE_LOG_PATH.read_text(encoding="utf-8")
	assert "[DB_WRITE] INSERT User" in db_content
	assert "[DB_WRITE] UPDATE User" in db_content
	assert "[DB_WRITE] DELETE User" in db_content
	# Ensure password hash is not exposed
	assert "StudentPassword123" not in db_content


def test_ai_agent_communication_logging() -> None:
	"""Verify that AI agent prompt and response communications are logged to ai_agent.log."""
	test_task = "test_case_synthesis_demo"
	system_prompt = "You are a competitive programming assistant."
	user_prompt = "Generate 10 test cases for Binary Search."
	model = "gpt-4o-mini"

	log_ai_prompt(test_task, system_prompt, user_prompt, model, provider="remote")

	response_json = json.dumps({"test_cases": [{"input": "5", "output": "25"}]})
	log_ai_response(test_task, response_json, duration_ms=450.5, success=True, model=model)

	assert AI_AGENT_LOG_PATH.exists()
	ai_content = AI_AGENT_LOG_PATH.read_text(encoding="utf-8")
	assert f"task={test_task}" in ai_content
	assert "Binary Search" in ai_content
	assert "[AI_RESPONSE]" in ai_content
	assert "SUCCESS" in ai_content
