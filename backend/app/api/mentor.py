from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import select

from app.api.utils import api_error, api_success, require_roles
from app.config import Config
from app.database import get_db_session
from app.models.assignment import CodeSubmission
from app.models.enums import (
	AIReviewStatus,
	AssignmentStatus,
	DifficultyLevel,
	QuestionSetStatus,
	TestCaseSource,
	UserRole,
)
from app.models.mentor import MentorAssignment
from app.models.question import CodingQuestion, CodingTestCase, MCQQuestion, QuestionSet
from app.services.ai_client import ai_service
from app.services.sanitizer import sanitize_text

mentor_bp: Blueprint = Blueprint("mentor", __name__, url_prefix="/api/v1/mentor")


@mentor_bp.route("/question-set/my-week", methods=["GET"])
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def get_my_week_question_set() -> tuple[Response, int]:
	"""Fetch or create the question set for the mentor's currently active assignment."""
	mentor_id: int = int(get_jwt_identity())
	today = datetime.now(Config.SYSTEM_TIMEZONE).date()

	with get_db_session() as session:
		stmt = select(MentorAssignment).where(
			MentorAssignment.user_id == mentor_id,
			MentorAssignment.week_start_date <= today,
			MentorAssignment.week_end_date >= today,
		)
		assignment: MentorAssignment | None = session.scalars(stmt).first()

		if not assignment:
			stmt_upcoming = (
				select(MentorAssignment)
				.where(
					MentorAssignment.user_id == mentor_id,
					MentorAssignment.status.in_(
						[AssignmentStatus.ACTIVE, AssignmentStatus.UPCOMING]
					),
				)
				.order_by(MentorAssignment.week_start_date.asc())
			)
			assignment = session.scalars(stmt_upcoming).first()

		if not assignment:
			return api_error(
				"NO_ASSIGNMENT",
				"No active or upcoming mentor rotation found for you.",
				status_code=404,
			)

		if not assignment.question_set:
			q_set = QuestionSet(
				mentor_assignment_id=assignment.id,
				week_start_date=assignment.week_start_date,
				status=QuestionSetStatus.DRAFT,
			)
			session.add(q_set)
			session.flush()
			assignment.question_set = q_set

		data: dict[str, Any] = assignment.question_set.to_dict()
		data["mcqs"] = [
			m.to_dict(include_answer=True) for m in assignment.question_set.mcq_questions
		]
		data["coding_questions"] = [
			c.to_dict(include_hidden_tests=True) for c in assignment.question_set.coding_questions
		]

		return api_success(data)


@mentor_bp.route("/questions/mcq", methods=["POST"])
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def add_mcq() -> tuple[Response, int]:
	"""Add an MCQ to the active question set."""
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data:
		return api_error("INVALID_PAYLOAD", "Request body must be valid JSON.")

	question_set_id: int | None = data.get("question_set_id")
	prompt_text: str = str(data.get("prompt_text", "")).strip()
	options: list[str] = data.get("options", [])
	correct_index: int | None = data.get("correct_option_index")
	explanation: str | None = data.get("explanation")
	difficulty_str: str = str(data.get("difficulty", "medium")).lower()

	if not question_set_id or not prompt_text or len(options) < 2 or correct_index is None:
		return api_error(
			"MISSING_FIELDS",
			"'question_set_id', 'prompt_text', 'options' (>=2), and 'correct_option_index' are required.",
		)

	if correct_index < 0 or correct_index >= len(options):
		return api_error("INVALID_INDEX", "correct_option_index is out of range.")

	safe_prompt: str = sanitize_text(prompt_text, max_length=4096, allow_html=True)
	safe_explanation: str | None = (
		sanitize_text(explanation, max_length=4096, allow_html=True) if explanation else None
	)
	safe_options: list[str] = [sanitize_text(opt, max_length=1024) for opt in options]

	with get_db_session() as session:
		q_set: QuestionSet | None = session.get(QuestionSet, question_set_id)
		if not q_set or q_set.status != QuestionSetStatus.DRAFT:
			return api_error(
				"INVALID_QUESTION_SET",
				"Question set must be in draft status to add questions.",
				status_code=400,
			)

		mcq = MCQQuestion(
			question_set_id=q_set.id,
			prompt_text=safe_prompt,
			options=safe_options,
			correct_option_index=correct_index,
			explanation=safe_explanation,
			difficulty=DifficultyLevel(difficulty_str)
			if difficulty_str in DifficultyLevel.__members__.values()
			else DifficultyLevel.MEDIUM,
		)
		session.add(mcq)
		session.flush()

		return api_success(mcq.to_dict(include_answer=True), message="MCQ created successfully.")


@mentor_bp.route("/questions/coding", methods=["POST"])
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def add_coding_question() -> tuple[Response, int]:
	"""Add a coding question with exactly 5 mentor-authored test cases."""
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data:
		return api_error("INVALID_PAYLOAD", "Request body must be valid JSON.")

	question_set_id: int | None = data.get("question_set_id")
	title: str = str(data.get("title", "")).strip()
	word_problem: str = str(data.get("word_problem_text", "")).strip()
	constraints: str = str(data.get("constraints_text", "")).strip()
	test_cases: list[dict[str, Any]] = data.get("test_cases", [])

	if not question_set_id or not title or not word_problem:
		return api_error(
			"MISSING_FIELDS", "'question_set_id', 'title', and 'word_problem_text' are required."
		)

	if len(test_cases) != 5:
		return api_error(
			"TEST_CASES_REQUIRED",
			f"Exactly 5 mentor-authored test cases are required (received {len(test_cases)}).",
		)

	safe_title: str = sanitize_text(title, max_length=255)
	safe_problem: str = sanitize_text(word_problem, max_length=16384, allow_html=True)
	safe_constraints: str = sanitize_text(constraints, max_length=4096, allow_html=True)

	with get_db_session() as session:
		q_set: QuestionSet | None = session.get(QuestionSet, question_set_id)
		if not q_set or q_set.status != QuestionSetStatus.DRAFT:
			return api_error(
				"INVALID_QUESTION_SET",
				"Question set must be in draft status to add questions.",
				status_code=400,
			)

		coding_q = CodingQuestion(
			question_set_id=q_set.id,
			title=safe_title,
			word_problem_text=safe_problem,
			constraints_text=safe_constraints,
			difficulty=DifficultyLevel.MEDIUM,
		)
		session.add(coding_q)
		session.flush()

		for idx, tc in enumerate(test_cases):
			new_tc = CodingTestCase(
				coding_question_id=coding_q.id,
				input_data=str(tc.get("input", "")),
				expected_output=str(tc.get("expected_output", "")),
				is_sample=(idx == 0),
				is_stress_case=False,
				source=TestCaseSource.MENTOR_MANUAL,
			)
			session.add(new_tc)

		session.flush()
		return api_success(
			coding_q.to_dict(include_hidden_tests=True), message="Coding question created."
		)


@mentor_bp.route("/questions/coding/ai-generate-tests", methods=["POST"])
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def generate_ai_stress_tests() -> tuple[Response, int]:
	"""Generate stress test cases using the local/remote LLM."""
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data:
		return api_error("INVALID_PAYLOAD", "Request body must be valid JSON.")

	title: str = str(data.get("title", ""))
	problem: str = str(data.get("word_problem_text", ""))
	constraints: str = str(data.get("constraints_text", ""))
	reference_solution: str | None = data.get("reference_solution")

	if not title or not problem:
		return api_error("MISSING_FIELDS", "'title' and 'word_problem_text' are required.")

	try:
		result = ai_service.generate_stress_test_cases(
			title=title,
			problem_text=problem,
			constraints_text=constraints,
			reference_solution=reference_solution,
		)
		return api_success(result.model_dump())
	except Exception as err:
		return api_error("AI_GENERATION_FAILED", str(err))


@mentor_bp.route("/question-set/publish", methods=["POST"])
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def publish_question_set() -> tuple[Response, int]:
	"""Publish question set after verifying pool size minimums."""
	data: dict[str, Any] | None = request.get_json(silent=True)
	question_set_id: int | None = data.get("question_set_id") if data else None

	if not question_set_id:
		return api_error("MISSING_FIELDS", "'question_set_id' is required.")

	with get_db_session() as session:
		q_set: QuestionSet | None = session.get(QuestionSet, question_set_id)
		if not q_set:
			return api_error("NOT_FOUND", "Question set not found.", status_code=404)

		if len(q_set.mcq_questions) < Config.MIN_MCQ_POOL_SIZE:
			return api_error(
				"INSUFFICIENT_MCQS",
				f"At least {Config.MIN_MCQ_POOL_SIZE} MCQs are required to publish (current: {len(q_set.mcq_questions)}).",
			)

		if len(q_set.coding_questions) < Config.MIN_CODING_POOL_SIZE:
			return api_error(
				"INSUFFICIENT_CODING",
				f"At least {Config.MIN_CODING_POOL_SIZE} coding questions are required to publish (current: {len(q_set.coding_questions)}).",
			)

		q_set.status = QuestionSetStatus.PUBLISHED
		return api_success(q_set.to_dict(), message="Question set published successfully.")


@mentor_bp.route("/flagged-submissions", methods=["GET"])
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def get_flagged_submissions() -> tuple[Response, int]:
	"""List AI-flagged code submissions for mentor/admin human review."""
	with get_db_session() as session:
		stmt = (
			select(CodeSubmission)
			.where(CodeSubmission.ai_review_status == AIReviewStatus.FLAGGED)
			.limit(50)
		)
		flagged = session.scalars(stmt).all()
		return api_success([sub.to_dict() for sub in flagged])


@mentor_bp.route("/flagged-submissions/<int:submission_id>/review", methods=["POST"])
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def review_flagged_submission(submission_id: int) -> tuple[Response, int]:
	"""Mentor or Admin human review of a flagged submission."""
	data: dict[str, Any] | None = request.get_json(silent=True)
	decision: str = str(data.get("decision", "")).lower() if data else ""
	notes: str = str(data.get("notes", "")) if data else ""

	if decision not in ("clean", "penalize", "dismiss"):
		return api_error("INVALID_DECISION", "Decision must be 'clean', 'penalize', or 'dismiss'.")

	with get_db_session() as session:
		sub: CodeSubmission | None = session.get(CodeSubmission, submission_id)
		if not sub:
			return api_error("NOT_FOUND", "Submission not found.", status_code=404)

		sub.ai_review_status = (
			AIReviewStatus.CLEAN if decision == "clean" else AIReviewStatus.FLAGGED
		)
		sub.ai_review_notes = notes
		return api_success(sub.to_dict(), message="Submission review updated.")
