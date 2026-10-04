from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from app.config import Config
from app.models.assignment import DailyAssignment
from app.models.enums import (
	AssignmentStatus,
	DifficultyLevel,
	ExecutionStatus,
	QuestionSetStatus,
)
from app.models.mentor import MentorAssignment
from app.models.question import (
	CodingHiddenTestCase,
	CodingQuestion,
	CodingSampleTestCase,
	MCQQuestion,
	QuestionSet,
)
from app.models.user import User
from app.services.judge0_client import Judge0ExecutionResult, judge0_service


def setup_challenge(db: Session, student: User, mentor: User) -> DailyAssignment:
	today = datetime.now(Config.SYSTEM_TIMEZONE).date()

	# Create mentor assignment & question set
	m_assign = MentorAssignment(
		user_id=mentor.id,
		week_start_date=today,
		week_end_date=today,
		status=AssignmentStatus.ACTIVE,
		created_by_admin_id=mentor.id,
	)
	db.add(m_assign)
	db.flush()

	q_set = QuestionSet(
		mentor_assignment_id=m_assign.id,
		week_start_date=today,
		status=QuestionSetStatus.PUBLISHED,
	)
	db.add(q_set)
	db.flush()

	# Add MCQ
	mcq = MCQQuestion(
		question_set_id=q_set.id,
		prompt_text="What is the time complexity of binary search?",
		options=["O(n)", "O(log n)", "O(n^2)", "O(1)"],
		correct_option_index=1,
		explanation="Binary search halves search space each step.",
		difficulty=DifficultyLevel.EASY,
	)
	db.add(mcq)
	db.flush()

	# Add Coding Question
	coding_q = CodingQuestion(
		question_set_id=q_set.id,
		title="Sum Two Numbers",
		word_problem_text="Given two integers, print their sum.",
		constraints_text="Integers fit in standard int.",
		difficulty=DifficultyLevel.EASY,
		allowed_languages=["python", "cpp"],
	)
	db.add(coding_q)
	db.flush()

	# Add 3 Sample Test Cases
	for i in range(1, 4):
		db.add(
			CodingSampleTestCase(
				coding_question_id=coding_q.id,
				input_data=f"{i} {i}",
				expected_output=f"{i + i}",
			)
		)

	# Add 10 Hidden Test Cases
	for i in range(4, 14):
		db.add(
			CodingHiddenTestCase(
				coding_question_id=coding_q.id,
				input_data=f"{i} 10",
				expected_output=f"{i + 10}",
			)
		)
	db.flush()

	# Add Daily Assignment
	assignment = DailyAssignment(
		student_id=student.id,
		assignment_date=today,
		mcq_question_id=mcq.id,
		coding_question_id=coding_q.id,
	)
	db.add(assignment)
	db.commit()
	return assignment


def test_mcq_submission(
	client: FlaskClient,
	db: Session,
	test_student_user: User,
	test_mentor_user: User,
	student_auth_headers: dict[str, str],
) -> None:
	assignment = setup_challenge(db, test_student_user, test_mentor_user)

	# Submit correct answer (index 1)
	res = client.post(
		"/api/student/daily/mcq-submit",
		headers=student_auth_headers,
		json={"assignment_id": assignment.id, "selected_option_index": 1},
	)
	assert res.status_code == 200
	data: dict[str, Any] = res.get_json()
	assert data["data"]["is_correct"] is True
	assert data["data"]["points_awarded"] == 5


def test_code_submission_security_block(
	client: FlaskClient,
	db: Session,
	test_student_user: User,
	test_mentor_user: User,
	student_auth_headers: dict[str, str],
) -> None:
	assignment = setup_challenge(db, test_student_user, test_mentor_user)

	# Malicious submission importing subprocess
	bad_code: str = "import subprocess\nsubprocess.call(['ls'])"
	res = client.post(
		"/api/student/daily/code-submit",
		headers=student_auth_headers,
		json={
			"assignment_id": assignment.id,
			"language": "python",
			"source_code": bad_code,
		},
	)
	assert res.status_code == 400
	data: dict[str, Any] = res.get_json()
	assert data["error"]["code"] == "SECURITY_VIOLATION"


def test_code_run_sample_cases_only(
	client: FlaskClient,
	db: Session,
	test_student_user: User,
	test_mentor_user: User,
	student_auth_headers: dict[str, str],
	monkeypatch: Any,
) -> None:
	assignment = setup_challenge(db, test_student_user, test_mentor_user)

	mock_result = Judge0ExecutionResult(
		status=ExecutionStatus.PASSED,
		stdout="2\n",
		stderr=None,
		compile_output=None,
		time_ms=30,
		memory_kb=1024,
		token="mock-run-token",
	)
	monkeypatch.setattr(judge0_service, "execute_submission", MagicMock(return_value=mock_result))

	code: str = "line = input().split()\nprint(int(line[0]) + int(line[1]))"
	res = client.post(
		"/api/student/daily/code-run",
		headers=student_auth_headers,
		json={
			"assignment_id": assignment.id,
			"language": "python",
			"source_code": code,
		},
	)
	assert res.status_code == 200
	data: dict[str, Any] = res.get_json()
	assert data["data"]["mode"] == "run"
	assert data["data"]["execution_status"] == "passed"
	# Evaluates ONLY 3 sample test cases!
	assert data["data"]["test_cases_passed"] == 3
	assert data["data"]["test_cases_total"] == 3


def test_code_submission_passed(
	client: FlaskClient,
	db: Session,
	test_student_user: User,
	test_mentor_user: User,
	student_auth_headers: dict[str, str],
	monkeypatch: Any,
) -> None:
	assignment = setup_challenge(db, test_student_user, test_mentor_user)

	# Mock Judge0 execution to simulate successful pass
	mock_result = Judge0ExecutionResult(
		status=ExecutionStatus.PASSED,
		stdout="8\n",
		stderr=None,
		compile_output=None,
		time_ms=45,
		memory_kb=1024,
		token="mock-token-123",
	)
	monkeypatch.setattr(judge0_service, "execute_submission", MagicMock(return_value=mock_result))

	valid_code: str = "line = input().split()\nprint(int(line[0]) + int(line[1]))"
	res = client.post(
		"/api/student/daily/code-submit",
		headers=student_auth_headers,
		json={
			"assignment_id": assignment.id,
			"language": "python",
			"source_code": valid_code,
		},
	)
	assert res.status_code == 200
	data: dict[str, Any] = res.get_json()
	assert data["data"]["execution_status"] == "passed"
	assert data["data"]["test_cases_passed"] == 13
	assert data["data"]["test_cases_total"] == 13
	assert data["data"]["points_awarded"] == 15
	assert data["data"]["submission_attempts_count"] == 1


def test_coding_session_start_and_timer(
	client: FlaskClient,
	db: Session,
	test_student_user: User,
	test_mentor_user: User,
	student_auth_headers: dict[str, str],
	monkeypatch: Any,
) -> None:
	assignment = setup_challenge(db, test_student_user, test_mentor_user)

	# 1. Start coding session
	start_res = client.post(
		"/api/student/daily/coding-session/start",
		headers=student_auth_headers,
		json={"assignment_id": assignment.id},
	)
	assert start_res.status_code == 200
	start_data = start_res.get_json()
	assert start_data["success"] is True
	assert start_data["data"]["coding_started_at"] is not None

	# 2. Get assignment by ID
	assign_res = client.get(
		f"/api/student/daily/assignment/{assignment.id}",
		headers=student_auth_headers,
	)
	assert assign_res.status_code == 200
	assign_data = assign_res.get_json()
	assert assign_data["data"]["id"] == assignment.id
	assert assign_data["data"]["coding_started_at"] is not None

	# 3. Submit solution and verify attempts count & time spent
	mock_result = Judge0ExecutionResult(
		status=ExecutionStatus.PASSED,
		stdout="8\n",
		stderr=None,
		compile_output=None,
		time_ms=50,
		memory_kb=1024,
		token="mock-token-session",
	)
	monkeypatch.setattr(judge0_service, "execute_submission", MagicMock(return_value=mock_result))

	sub_res = client.post(
		"/api/student/daily/code-submit",
		headers=student_auth_headers,
		json={
			"assignment_id": assignment.id,
			"language": "python",
			"source_code": "line = input().split()\nprint(int(line[0]) + int(line[1]))",
		},
	)
	assert sub_res.status_code == 200
	sub_data = sub_res.get_json()
	assert sub_data["data"]["submission_attempts_count"] == 1
	assert sub_data["data"]["coding_time_spent_seconds"] is not None
	assert sub_data["data"]["coding_time_spent_seconds"] >= 0

