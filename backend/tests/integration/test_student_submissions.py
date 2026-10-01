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
	TestCaseSource,
)
from app.models.mentor import MentorAssignment
from app.models.question import CodingQuestion, CodingTestCase, MCQQuestion, QuestionSet
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

	tc = CodingTestCase(
		coding_question_id=coding_q.id,
		input_data="3 5",
		expected_output="8",
		is_sample=True,
		source=TestCaseSource.MENTOR_MANUAL,
	)
	db.add(tc)
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
		"/api/v1/student/daily/mcq-submit",
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
		"/api/v1/student/daily/code-submit",
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
		"/api/v1/student/daily/code-submit",
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
	assert data["data"]["test_cases_passed"] == 1
	assert data["data"]["points_awarded"] == 15
