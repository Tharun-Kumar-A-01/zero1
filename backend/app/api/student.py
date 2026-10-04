from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
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
from app.models.question import CodingQuestion, MCQQuestion
from app.models.user import User
from app.services.ai_client import ai_service
from app.services.code_analyzer import analyze_student_code
from app.services.code_harness import prepare_code_for_execution
from app.services.judge0_client import Judge0ExecutionResult, judge0_service
from app.services.rotation_service import generate_daily_assignments_for_date
from app.services.sanitizer import sanitize_code
from app.services.streak_service import evaluate_daily_streak_and_points, get_student_total_points

student_bp: Blueprint = Blueprint("student", __name__, url_prefix="/api/student")


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


@student_bp.route("/daily/assignment/<int:assignment_id>", methods=["GET"])
@jwt_required()
@require_roles(UserRole.STUDENT, UserRole.ADMIN)
def get_assignment_by_id(assignment_id: int) -> tuple[Response, int]:
	"""Fetch specific daily assignment by ID."""
	student_id: int = int(get_jwt_identity())
	with get_db_session() as session:
		assignment: DailyAssignment | None = session.get(DailyAssignment, assignment_id)
		if assignment is None:
			return api_error("NOT_FOUND", "Assignment not found.", status_code=404)
		if assignment.student_id != student_id and get_jwt().get("role") != UserRole.ADMIN.value:
			return api_error("FORBIDDEN", "You do not have access to this assignment.", status_code=403)
		return api_success(assignment.to_dict())


@student_bp.route("/daily/coding-session/start", methods=["POST"])
@jwt_required()
@require_roles(UserRole.STUDENT)
def start_coding_session() -> tuple[Response, int]:
	"""Record the start of a coding session for an assignment. Discards any previous start timestamp."""
	student_id: int = int(get_jwt_identity())
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data or not data.get("assignment_id"):
		return api_error("INVALID_PAYLOAD", "'assignment_id' is required.")

	assignment_id: int = int(data["assignment_id"])
	with get_db_session() as session:
		assignment: DailyAssignment | None = session.get(DailyAssignment, assignment_id)
		if assignment is None or assignment.student_id != student_id:
			return api_error("NOT_FOUND", "Assignment not found for current student.", status_code=404)

		now = datetime.now(UTC)
		if assignment.coding_started_at is None:
			assignment.coding_started_at = now
			session.flush()

		started_at = assignment.coding_started_at
		if started_at.tzinfo is None:
			started_at = started_at.replace(tzinfo=UTC)

		elapsed_seconds = max(0, int((now - started_at).total_seconds()))

		return api_success(
			{
				"assignment_id": assignment.id,
				"coding_started_at": started_at.isoformat(),
				"coding_completed_at": assignment.coding_completed_at.isoformat() if assignment.coding_completed_at else None,
				"coding_time_spent_seconds": assignment.coding_time_spent_seconds,
				"elapsed_seconds": elapsed_seconds,
				"submission_attempts_count": assignment.submission_attempts_count,
				"coding_status": assignment.coding_status.value,
			},
			message="Coding session active.",
		)


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


@student_bp.route("/daily/code-run", methods=["POST"])
@jwt_required()
@require_roles(UserRole.STUDENT)
@rate_limit(limit=30, window_seconds=60, key_prefix="run:code")
def run_daily_code() -> tuple[Response, int]:
	"""Run student code against ONLY the 3 sample test cases without marking as solved or awarding points."""
	student_id: int = int(get_jwt_identity())
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data:
		return api_error("INVALID_PAYLOAD", "Request body must be valid JSON.")

	assignment_id: int | None = data.get("assignment_id")
	language: str = str(data.get("language", "")).lower().strip()
	raw_code: str = str(data.get("source_code", "")).strip()

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

		sample_cases: list[Any] = list(coding_q.sample_test_cases)
		if not sample_cases and coding_q.legacy_test_cases:
			sample_cases = [tc for tc in coding_q.legacy_test_cases if tc.is_sample]

		if not sample_cases:
			# Fallback to all available test cases if none marked as sample
			sample_cases = list(coding_q.test_cases)

		executable_code: str = prepare_code_for_execution(
			source_code=clean_code,
			language=language,
			function_name=coding_q.function_name,
			parameter_definitions=coding_q.parameter_definitions,
			return_type=coding_q.return_type,
		)

		passed_count: int = 0
		total_count: int = len(sample_cases)
		test_case_results: list[dict[str, Any]] = []
		first_failed_status: ExecutionStatus | None = None
		first_error_msg: str | None = None
		first_compile_output: str | None = None
		max_runtime_ms: int = 0
		max_memory_kb: int = 0

		for idx, test_case in enumerate(sample_cases):
			result: Judge0ExecutionResult = judge0_service.execute_submission(
				source_code=executable_code,
				language=language,
				stdin=test_case.input_data,
				expected_output=test_case.expected_output,
				cpu_time_limit=float(coding_q.time_limit_ms) / 1000.0,
				memory_limit_kb=coding_q.memory_limit_kb,
			)

			if result.time_ms and result.time_ms > max_runtime_ms:
				max_runtime_ms = result.time_ms
			if result.memory_kb and result.memory_kb > max_memory_kb:
				max_memory_kb = result.memory_kb

			is_passed: bool = result.status == ExecutionStatus.PASSED
			if is_passed:
				passed_count += 1
			elif first_failed_status is None:
				first_failed_status = result.status
				first_error_msg = result.stderr or result.compile_output
				first_compile_output = result.compile_output

			case_status_str: str = "passed" if is_passed else result.status.value
			test_case_results.append(
				{
					"case_number": idx + 1,
					"status": case_status_str,
					"input": test_case.input_data,
					"expected_output": (test_case.expected_output or "").strip(),
					"actual_output": (result.stdout or "").strip(),
					"error_message": result.stderr or result.compile_output or None,
					"runtime_ms": result.time_ms,
					"memory_kb": result.memory_kb,
				}
			)

			if result.status == ExecutionStatus.COMPILATION_ERROR:
				for rem_idx in range(idx + 1, total_count):
					rem_case = sample_cases[rem_idx]
					test_case_results.append(
						{
							"case_number": rem_idx + 1,
							"status": "compilation_error",
							"input": rem_case.input_data,
							"expected_output": (rem_case.expected_output or "").strip(),
							"actual_output": "",
							"error_message": result.stderr or result.compile_output or None,
							"runtime_ms": None,
							"memory_kb": None,
						}
					)
				break

		overall_status: ExecutionStatus = (
			ExecutionStatus.PASSED
			if (passed_count == total_count and total_count > 0)
			else (first_failed_status or ExecutionStatus.FAILED)
		)

		return api_success(
			{
				"mode": "run",
				"execution_status": overall_status.value,
				"test_cases_passed": passed_count,
				"test_cases_total": total_count,
				"runtime_ms": max_runtime_ms if max_runtime_ms > 0 else None,
				"memory_kb": max_memory_kb if max_memory_kb > 0 else None,
				"compiler_output": first_compile_output,
				"error_message": first_error_msg,
				"test_case_results": test_case_results,
			},
			message="Sample test cases executed.",
		)


@student_bp.route("/daily/code-submit", methods=["POST"])
@jwt_required()
@require_roles(UserRole.STUDENT)
@rate_limit(limit=10, window_seconds=60, key_prefix="submit:code")
def submit_daily_code() -> tuple[Response, int]:
	"""Submit student code: Phase 1 (Sample), Phase 2 (Hidden), Phase 3 (AI Anti-cheat Review)."""
	student_id: int = int(get_jwt_identity())
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data:
		return api_error("INVALID_PAYLOAD", "Request body must be valid JSON.")

	assignment_id: int | None = data.get("assignment_id")
	language: str = str(data.get("language", "")).lower().strip()
	raw_code: str = str(data.get("source_code", "")).strip()

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

		# Distinct sample and hidden test case lists
		sample_cases: list[Any] = list(coding_q.sample_test_cases)
		hidden_cases: list[Any] = list(coding_q.hidden_test_cases)

		# Fallback to legacy test cases if neither table has records
		if not sample_cases and not hidden_cases and coding_q.legacy_test_cases:
			sample_cases = [tc for tc in coding_q.legacy_test_cases if tc.is_sample]
			hidden_cases = [tc for tc in coding_q.legacy_test_cases if not tc.is_sample]

		if not sample_cases and not hidden_cases:
			sample_cases = list(coding_q.test_cases)

		total_test_count = len(sample_cases) + len(hidden_cases)

		# Increment submission attempts
		assignment.submission_attempts_count += 1

		executable_code: str = prepare_code_for_execution(
			source_code=clean_code,
			language=language,
			function_name=coding_q.function_name,
			parameter_definitions=coding_q.parameter_definitions,
			return_type=coding_q.return_type,
		)

		# ========================================================
		# Phase 1: Validate 3 Sample Test Cases First
		# ========================================================
		passed_sample_count = 0
		last_result: Judge0ExecutionResult | None = None
		sample_case_results: list[dict[str, Any]] = []

		for idx, test_case in enumerate(sample_cases):
			result = judge0_service.execute_submission(
				source_code=executable_code,
				language=language,
				stdin=test_case.input_data,
				expected_output=test_case.expected_output,
				cpu_time_limit=float(coding_q.time_limit_ms) / 1000.0,
				memory_limit_kb=coding_q.memory_limit_kb,
			)
			last_result = result
			is_passed = result.status == ExecutionStatus.PASSED
			if is_passed:
				passed_sample_count += 1

			sample_case_results.append(
				{
					"case_number": idx + 1,
					"status": "passed" if is_passed else result.status.value,
					"input": test_case.input_data,
					"expected_output": (test_case.expected_output or "").strip(),
					"actual_output": (result.stdout or "").strip(),
					"error_message": result.stderr or result.compile_output or None,
					"runtime_ms": result.time_ms,
					"memory_kb": result.memory_kb,
				}
			)
			if not is_passed:
				break

		if passed_sample_count < len(sample_cases):
			# Failed during sample test cases
			assignment.coding_status = DailyCodingStatus.ATTEMPTED_UNSOLVED
			submission = CodeSubmission(
				daily_assignment_id=assignment.id,
				language=language,
				source_code=clean_code,
				judge0_token=last_result.token if last_result else None,
				execution_status=last_result.status if last_result else ExecutionStatus.FAILED,
				test_cases_passed_count=passed_sample_count,
				test_cases_total_count=total_test_count,
				runtime_ms=last_result.time_ms if last_result else None,
				memory_kb=last_result.memory_kb if last_result else None,
				compiler_output=last_result.compile_output or last_result.stderr if last_result else None,
				ai_review_status=AIReviewStatus.PENDING,
			)
			session.add(submission)
			session.flush()
			return api_success(
				{
					"mode": "submit",
					"phase": "sample",
					"execution_status": last_result.status.value if last_result else "failed",
					"test_cases_passed": passed_sample_count,
					"test_cases_total": total_test_count,
					"runtime_ms": last_result.time_ms if last_result else None,
					"memory_kb": last_result.memory_kb if last_result else None,
					"compiler_output": last_result.compile_output if last_result else None,
					"error_message": f"Sample test case #{passed_sample_count + 1} failed: {last_result.stderr or 'Output mismatch'}"
					if last_result else "Sample test case failed.",
					"points_awarded": 0,
					"current_streak": 0,
					"is_day_solved": False,
					"submission_attempts_count": assignment.submission_attempts_count,
					"test_case_results": sample_case_results,
				},
				message="Solution failed on sample test cases.",
			)

		# ========================================================
		# Phase 2: Validate 10 Hidden Test Cases
		# ========================================================
		passed_hidden_count = 0
		for test_case in hidden_cases:
			result = judge0_service.execute_submission(
				source_code=executable_code,
				language=language,
				stdin=test_case.input_data,
				expected_output=test_case.expected_output,
				cpu_time_limit=float(coding_q.time_limit_ms) / 1000.0,
				memory_limit_kb=coding_q.memory_limit_kb,
			)
			last_result = result
			if result.status == ExecutionStatus.PASSED:
				passed_hidden_count += 1
			else:
				break

		total_passed = passed_sample_count + passed_hidden_count

		if passed_hidden_count < len(hidden_cases):
			# Failed during hidden test cases
			assignment.coding_status = DailyCodingStatus.ATTEMPTED_UNSOLVED
			submission = CodeSubmission(
				daily_assignment_id=assignment.id,
				language=language,
				source_code=clean_code,
				judge0_token=last_result.token if last_result else None,
				execution_status=last_result.status if last_result else ExecutionStatus.FAILED,
				test_cases_passed_count=total_passed,
				test_cases_total_count=total_test_count,
				runtime_ms=last_result.time_ms if last_result else None,
				memory_kb=last_result.memory_kb if last_result else None,
				compiler_output=last_result.compile_output or last_result.stderr if last_result else None,
				ai_review_status=AIReviewStatus.PENDING,
			)
			session.add(submission)
			session.flush()
			return api_success(
				{
					"mode": "submit",
					"phase": "hidden",
					"execution_status": last_result.status.value if last_result else "failed",
					"test_cases_passed": total_passed,
					"test_cases_total": total_test_count,
					"runtime_ms": last_result.time_ms if last_result else None,
					"memory_kb": last_result.memory_kb if last_result else None,
					"compiler_output": last_result.compile_output if last_result else None,
					"error_message": f"Hidden test case #{passed_hidden_count + 1} failed. Review standard constraints and algorithmic correctness.",
					"points_awarded": 0,
					"current_streak": 0,
					"is_day_solved": False,
					"submission_attempts_count": assignment.submission_attempts_count,
				},
				message="Solution failed on hidden test cases.",
			)

		# ========================================================
		# Phase 3: AI Code Audit for Hardcoding & Bruteforcing
		# ========================================================
		sample_dicts = [
			{"input": tc.input_data, "expected_output": tc.expected_output}
			for tc in sample_cases
		]

		ai_flagged = False
		ai_review_notes: str | None = None
		try:
			ai_res = ai_service.review_code_for_hardcoding(
				problem_title=coding_q.title,
				problem_text=coding_q.word_problem_text,
				student_code=clean_code,
				sample_cases=sample_dicts,
			)
			if ai_res.status == "flagged":
				ai_flagged = True
				ai_review_notes = ai_res.reason or "Hardcoded responses or lookup shortcuts detected."
		except Exception:
			# If AI review service is temporarily unreachable, do not hard-block passing solution
			ai_flagged = False

		if ai_flagged:
			assignment.coding_status = DailyCodingStatus.ATTEMPTED_UNSOLVED
			submission = CodeSubmission(
				daily_assignment_id=assignment.id,
				language=language,
				source_code=clean_code,
				judge0_token=last_result.token if last_result else None,
				execution_status=ExecutionStatus.PASSED,
				test_cases_passed_count=total_passed,
				test_cases_total_count=total_test_count,
				runtime_ms=last_result.time_ms if last_result else None,
				memory_kb=last_result.memory_kb if last_result else None,
				compiler_output=last_result.compile_output if last_result else None,
				ai_review_status=AIReviewStatus.FLAGGED,
				ai_review_notes=ai_review_notes,
			)
			session.add(submission)
			session.flush()
			return api_success(
				{
					"mode": "submit",
					"phase": "review",
					"execution_status": "flagged",
					"ai_flagged": True,
					"ai_review_notes": ai_review_notes,
					"test_cases_passed": total_passed,
					"test_cases_total": total_test_count,
					"runtime_ms": last_result.time_ms if last_result else None,
					"memory_kb": last_result.memory_kb if last_result else None,
					"compiler_output": last_result.compile_output if last_result else None,
					"error_message": f"Academic Integrity Alert: {ai_review_notes}",
					"points_awarded": 0,
					"current_streak": 0,
					"is_day_solved": False,
					"submission_attempts_count": assignment.submission_attempts_count,
				},
				message="Code passed execution, but was flagged by AI academic integrity review.",
			)

		# All tests passed and code integrity verified!
		now = datetime.now(UTC)
		if assignment.coding_started_at:
			started_at = assignment.coding_started_at
			if started_at.tzinfo is None:
				started_at = started_at.replace(tzinfo=UTC)
			assignment.coding_time_spent_seconds = max(
				0, int((now - started_at).total_seconds())
			)
		assignment.coding_completed_at = now
		assignment.coding_status = DailyCodingStatus.SOLVED
		submission = CodeSubmission(
			daily_assignment_id=assignment.id,
			language=language,
			source_code=clean_code,
			judge0_token=last_result.token if last_result else None,
			execution_status=ExecutionStatus.PASSED,
			test_cases_passed_count=total_passed,
			test_cases_total_count=total_test_count,
			runtime_ms=last_result.time_ms if last_result else None,
			memory_kb=last_result.memory_kb if last_result else None,
			compiler_output=last_result.compile_output if last_result else None,
			ai_review_status=AIReviewStatus.CLEAN,
		)
		session.add(submission)
		session.flush()

		current_streak, points_awarded, is_day_solved = evaluate_daily_streak_and_points(
			session=session, student_id=student_id, assignment_date=assignment.assignment_date
		)

		return api_success(
			{
				"mode": "submit",
				"execution_status": ExecutionStatus.PASSED.value,
				"test_cases_passed": total_passed,
				"test_cases_total": total_test_count,
				"runtime_ms": last_result.time_ms if last_result else None,
				"memory_kb": last_result.memory_kb if last_result else None,
				"compiler_output": last_result.compile_output if last_result else None,
				"error_message": None,
				"points_awarded": points_awarded,
				"current_streak": current_streak,
				"is_day_solved": is_day_solved,
				"coding_time_spent_seconds": assignment.coding_time_spent_seconds,
				"submission_attempts_count": assignment.submission_attempts_count,
			},
			message="Code evaluated and verified successfully.",
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
