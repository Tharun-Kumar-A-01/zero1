from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func, select

from app.api.utils import api_error, api_success, rate_limit, require_roles
from app.config import Config
from app.database import get_db_session
from app.models.assignment import CodeSubmission, DailyAssignment, MCQSubmission
from app.models.enums import (
	AIReviewStatus,
	DailyCodingStatus,
	DailyMCQStatus,
	ExecutionStatus,
	UserRole,
)
from app.models.gamification import PointsLedger, Streak, StudentReward
from app.models.question import CodingQuestion, CodingTestCase, MCQQuestion
from app.models.user import User
from app.services.code_analyzer import analyze_student_code
from app.services.judge0_client import Judge0ExecutionResult, judge0_service
from app.services.rotation_service import generate_daily_assignments_for_date
from app.services.sanitizer import sanitize_code
from app.services.streak_service import evaluate_daily_streak_and_points, get_student_total_points

student_bp: Blueprint = Blueprint("student", __name__, url_prefix="/api/v1/student")


@student_bp.route("/daily/today", methods=["GET"])
@jwt_required()
@require_roles(UserRole.STUDENT)
def get_daily_challenge() -> tuple[Response, int]:
	"""Fetch today's randomized challenge for the authenticated student."""
	student_id: int = int(get_jwt_identity())
	today = datetime.now(Config.SYSTEM_TIMEZONE).date()

	with get_db_session() as session:
		stmt = select(DailyAssignment).where(
			DailyAssignment.student_id == student_id, DailyAssignment.assignment_date == today
		)
		assignment: DailyAssignment | None = session.scalars(stmt).first()

		if assignment is None:
			generate_daily_assignments_for_date(session, today)
			assignment = session.scalars(stmt).first()

		if assignment is None:
			return api_error(
				"NO_CHALLENGE_AVAILABLE",
				"No practice challenges are currently available for today. Please check back soon.",
				status_code=404,
			)

		return api_success(assignment.to_dict())


@student_bp.route("/daily/mcq-submit", methods=["POST"])
@jwt_required()
@require_roles(UserRole.STUDENT)
@rate_limit(limit=10, window_seconds=60, key_prefix="submit:mcq")
def submit_mcq() -> tuple[Response, int]:
	"""Submit an answer to today's MCQ challenge."""
	student_id: int = int(get_jwt_identity())
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data:
		return api_error("INVALID_PAYLOAD", "Request body must be valid JSON.")

	assignment_id: int | None = data.get("assignment_id")
	selected_option: int | None = data.get("selected_option_index")

	if assignment_id is None or selected_option is None:
		return api_error(
			"MISSING_FIELDS", "'assignment_id' and 'selected_option_index' are required."
		)

	with get_db_session() as session:
		assignment: DailyAssignment | None = session.get(DailyAssignment, assignment_id)
		if assignment is None or assignment.student_id != student_id:
			return api_error(
				"NOT_FOUND", "Assignment not found for current student.", status_code=404
			)

		if assignment.mcq_question_id is None:
			return api_error("NO_MCQ", "No MCQ assigned for this challenge.")

		mcq: MCQQuestion | None = session.get(MCQQuestion, assignment.mcq_question_id)
		if mcq is None:
			return api_error(
				"QUESTION_NOT_FOUND", "MCQ question record not found.", status_code=404
			)

		is_correct: bool = selected_option == mcq.correct_option_index
		assignment.mcq_status = DailyMCQStatus.CORRECT if is_correct else DailyMCQStatus.INCORRECT

		submission = MCQSubmission(
			daily_assignment_id=assignment.id,
			selected_option_index=selected_option,
			is_correct=is_correct,
		)
		session.add(submission)
		session.flush()

		current_streak, points_awarded, is_day_solved = evaluate_daily_streak_and_points(
			session=session, student_id=student_id, assignment_date=assignment.assignment_date
		)

		return api_success(
			{
				"is_correct": is_correct,
				"explanation": mcq.explanation if is_correct else None,
				"points_awarded": points_awarded,
				"current_streak": current_streak,
				"is_day_solved": is_day_solved,
			},
			message="MCQ submitted successfully.",
		)


@student_bp.route("/daily/code-submit", methods=["POST"])
@jwt_required()
@require_roles(UserRole.STUDENT)
@rate_limit(limit=5, window_seconds=60, key_prefix="submit:code")
def submit_code() -> tuple[Response, int]:
	"""Submit code solution, run static pre-check, and execute against Judge0 test cases."""
	student_id: int = int(get_jwt_identity())
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data:
		return api_error("INVALID_PAYLOAD", "Request body must be valid JSON.")

	assignment_id: int | None = data.get("assignment_id")
	language: str = str(data.get("language", "")).strip().lower()
	raw_code: str = str(data.get("source_code", ""))

	if not assignment_id or not language or not raw_code:
		return api_error(
			"MISSING_FIELDS", "'assignment_id', 'language', and 'source_code' are required."
		)

	try:
		clean_code: str = sanitize_code(raw_code, max_bytes=65536)
	except Exception as err:
		return api_error("SANITIZATION_FAILED", str(err))

	with get_db_session() as session:
		assignment: DailyAssignment | None = session.get(DailyAssignment, assignment_id)
		if assignment is None or assignment.student_id != student_id:
			return api_error(
				"NOT_FOUND", "Assignment not found for current student.", status_code=404
			)

		if assignment.coding_question_id is None:
			return api_error("NO_CODING_PROBLEM", "No coding question assigned for this challenge.")

		coding_q: CodingQuestion | None = session.get(CodingQuestion, assignment.coding_question_id)
		if coding_q is None:
			return api_error(
				"QUESTION_NOT_FOUND", "Coding question record not found.", status_code=404
			)

		if language not in [lang.lower() for lang in coding_q.allowed_languages]:
			return api_error(
				"LANGUAGE_NOT_ALLOWED",
				f"Language '{language}' is not permitted for this problem. Allowed: {', '.join(coding_q.allowed_languages)}",
			)

		is_safe, error_msg = analyze_student_code(
			code=clean_code, language=language, forbidden_constructs=coding_q.forbidden_constructs
		)
		if not is_safe:
			return api_error(
				"SECURITY_VIOLATION",
				error_msg or "Forbidden constructs detected in submitted code.",
			)

		test_cases: list[CodingTestCase] = list(coding_q.test_cases)
		passed_count: int = 0
		total_count: int = len(test_cases)
		last_result: Judge0ExecutionResult | None = None

		for test_case in test_cases:
			result: Judge0ExecutionResult = judge0_service.execute_submission(
				source_code=clean_code,
				language=language,
				stdin=test_case.input_data,
				expected_output=test_case.expected_output,
				cpu_time_limit=float(coding_q.time_limit_ms) / 1000.0,
				memory_limit_kb=coding_q.memory_limit_kb,
			)
			last_result = result
			if result.status == ExecutionStatus.PASSED:
				passed_count += 1
			else:
				break

		overall_status: ExecutionStatus = (
			ExecutionStatus.PASSED
			if (passed_count == total_count and total_count > 0)
			else (last_result.status if last_result else ExecutionStatus.FAILED)
		)

		if overall_status == ExecutionStatus.PASSED:
			assignment.coding_status = DailyCodingStatus.SOLVED
		else:
			assignment.coding_status = DailyCodingStatus.ATTEMPTED_UNSOLVED

		submission = CodeSubmission(
			daily_assignment_id=assignment.id,
			language=language,
			source_code=clean_code,
			judge0_token=last_result.token if last_result else None,
			execution_status=overall_status,
			test_cases_passed_count=passed_count,
			test_cases_total_count=total_count,
			runtime_ms=last_result.time_ms if last_result else None,
			memory_kb=last_result.memory_kb if last_result else None,
			compiler_output=last_result.compile_output or last_result.stderr
			if last_result
			else None,
			ai_review_status=AIReviewStatus.PENDING,
		)
		session.add(submission)
		session.flush()

		current_streak, points_awarded, is_day_solved = evaluate_daily_streak_and_points(
			session=session, student_id=student_id, assignment_date=assignment.assignment_date
		)

		return api_success(
			{
				"execution_status": overall_status.value,
				"test_cases_passed": passed_count,
				"test_cases_total": total_count,
				"runtime_ms": last_result.time_ms if last_result else None,
				"memory_kb": last_result.memory_kb if last_result else None,
				"compiler_output": last_result.compile_output if last_result else None,
				"error_message": last_result.stderr
				if last_result and overall_status != ExecutionStatus.PASSED
				else None,
				"points_awarded": points_awarded,
				"current_streak": current_streak,
				"is_day_solved": is_day_solved,
			},
			message="Code evaluated successfully.",
		)


@student_bp.route("/progress", methods=["GET"])
@jwt_required()
@require_roles(UserRole.STUDENT)
def get_progress() -> tuple[Response, int]:
	"""Retrieve streak, points breakdown, and earned badges."""
	student_id: int = int(get_jwt_identity())
	with get_db_session() as session:
		streak_record = session.scalars(
			select(Streak).where(Streak.student_id == student_id)
		).first()
		total_points: int = get_student_total_points(session, student_id)

		stmt_rewards = select(StudentReward).where(StudentReward.student_id == student_id)
		earned_rewards = session.scalars(stmt_rewards).all()

		return api_success(
			{
				"current_streak": streak_record.current_streak if streak_record else 0,
				"longest_streak": streak_record.longest_streak if streak_record else 0,
				"last_active_date": streak_record.last_active_date.isoformat()
				if streak_record and streak_record.last_active_date
				else None,
				"total_points": total_points,
				"badges": [r.to_dict() for r in earned_rewards],
			}
		)


@student_bp.route("/leaderboard", methods=["GET"])
@jwt_required()
def get_leaderboard() -> tuple[Response, int]:
	"""Retrieve leaderboard scoped by year_batch."""
	user_id: int = int(get_jwt_identity())
	with get_db_session() as session:
		current_user: User | None = session.get(User, user_id)
		batch: str | None = request.args.get("year_batch") or (
			current_user.year_batch if current_user else None
		)

		query = (
			select(
				User.id,
				User.name,
				User.roll_number,
				User.year_batch,
				User.department,
				func.coalesce(func.sum(PointsLedger.delta), 0).label("total_points"),
				func.coalesce(Streak.current_streak, 0).label("current_streak"),
			)
			.outerjoin(PointsLedger, PointsLedger.student_id == User.id)
			.outerjoin(Streak, Streak.student_id == User.id)
			.where(User.role == UserRole.STUDENT, User.is_active.is_(True))
		)

		if batch:
			query = query.where(User.year_batch == batch)

		query = (
			query.group_by(User.id, Streak.current_streak)
			.order_by(func.sum(PointsLedger.delta).desc())
			.limit(50)
		)
		results = session.execute(query).all()

		leaderboard: list[dict[str, Any]] = [
			{
				"rank": idx + 1,
				"student_id": row.id,
				"name": row.name,
				"roll_number": row.roll_number,
				"year_batch": row.year_batch,
				"department": row.department,
				"total_points": row.total_points,
				"current_streak": row.current_streak,
			}
			for idx, row in enumerate(results)
		]

		return api_success(leaderboard)
