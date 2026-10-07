from __future__ import annotations

import csv
import io
import os
import time
from datetime import datetime
from typing import Any, cast

import openpyxl
from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.utils import api_error, api_success, require_roles
from app.config import Config
from app.database import get_db_session
from app.models.assignment import CodeSubmission
from app.models.enums import (
	AIReviewStatus,
	AssignmentStatus,
	DifficultyLevel,
	QuestionSetStatus,
	UserRole,
)
from app.models.mentor import MentorAssignment
from app.models.question import (
	CodingHiddenTestCase,
	CodingQuestion,
	CodingSampleTestCase,
	MCQQuestion,
	QuestionSet,
)
from app.services.ai_client import TestCaseModel, ai_service
from app.services.sanitizer import sanitize_text

mentor_bp: Blueprint = Blueprint("mentor", __name__, url_prefix="/api/mentor")


def serialize_question_set(q_set: QuestionSet) -> dict[str, Any]:
	"""Serialize a question set including MCQs and coding questions with tests."""
	data = q_set.to_dict()
	data["mcqs"] = [m.to_dict(include_answer=True) for m in q_set.mcq_questions]
	data["coding_questions"] = [
		c.to_dict(include_hidden_tests=True) for c in q_set.coding_questions
	]
	return data


def _get_or_create_active_question_set(
	session: Session, mentor_id: int, auto_create_draft: bool = True
) -> QuestionSet | None:
	"""Retrieve or create draft question set for mentor.

	Priority:
	1. Active or upcoming rotation assignment for this mentor that has an existing DRAFT question set.
	2. Unassigned DRAFT question set authored by this mentor.
	3. Upcoming rotation assignment for this mentor without a question set (provisions DRAFT set).
	4. Active rotation question set (even if PUBLISHED, for review).
	5. If auto_create_draft is True: create an unassigned DRAFT question set for this mentor.
	"""
	today = datetime.now(Config.SYSTEM_TIMEZONE).date()

	# 1. Check for draft question set in active or upcoming assignment
	stmt_assigned_draft = (
		select(QuestionSet)
		.join(MentorAssignment, QuestionSet.mentor_assignment_id == MentorAssignment.id)
		.where(
			MentorAssignment.user_id == mentor_id,
			MentorAssignment.status.in_([AssignmentStatus.ACTIVE, AssignmentStatus.UPCOMING]),
			QuestionSet.status == QuestionSetStatus.DRAFT,
		)
		.order_by(MentorAssignment.week_start_date.asc())
	)
	assigned_draft = session.scalars(stmt_assigned_draft).first()
	if assigned_draft:
		return cast(QuestionSet | None, assigned_draft)

	# 2. Check for unassigned draft question set authored by mentor
	stmt_unassigned_draft = (
		select(QuestionSet)
		.where(
			QuestionSet.mentor_id == mentor_id,
			QuestionSet.mentor_assignment_id.is_(None),
			QuestionSet.status == QuestionSetStatus.DRAFT,
		)
		.order_by(QuestionSet.id.desc())
	)
	unassigned_draft = session.scalars(stmt_unassigned_draft).first()
	if unassigned_draft:
		return cast(QuestionSet | None, unassigned_draft)

	# 3. Check for upcoming assignment that needs a question set created
	stmt_upcoming = (
		select(MentorAssignment)
		.where(
			MentorAssignment.user_id == mentor_id,
			MentorAssignment.status.in_([AssignmentStatus.ACTIVE, AssignmentStatus.UPCOMING]),
			MentorAssignment.week_start_date >= today,
		)
		.order_by(MentorAssignment.week_start_date.asc())
	)
	upcoming_assignment = session.scalars(stmt_upcoming).first()
	if upcoming_assignment:
		if not upcoming_assignment.question_set:
			q_set = QuestionSet(
				mentor_id=mentor_id,
				mentor_assignment_id=upcoming_assignment.id,
				week_start_date=upcoming_assignment.week_start_date,
				status=QuestionSetStatus.DRAFT,
			)
			session.add(q_set)
			session.flush()
			return q_set
		elif upcoming_assignment.question_set.status == QuestionSetStatus.DRAFT:
			return cast(QuestionSet | None, upcoming_assignment.question_set)

	# 4. Check for active assignment's question set (e.g. published current week for review)
	stmt_active = (
		select(MentorAssignment)
		.where(
			MentorAssignment.user_id == mentor_id,
			MentorAssignment.week_start_date <= today,
			MentorAssignment.week_end_date >= today,
			MentorAssignment.status == AssignmentStatus.ACTIVE,
		)
	)
	active_assignment = session.scalars(stmt_active).first()
	if active_assignment and active_assignment.question_set and not auto_create_draft:
		return cast(QuestionSet | None, active_assignment.question_set)

	# 5. If auto_create_draft is requested, create an unassigned DRAFT question set
	if auto_create_draft:
		q_set = QuestionSet(
			mentor_id=mentor_id,
			mentor_assignment_id=None,
			week_start_date=None,
			status=QuestionSetStatus.DRAFT,
		)
		session.add(q_set)
		session.flush()
		return q_set

	return None


@mentor_bp.route("/question-set/my-week", methods=["GET"], strict_slashes=False)
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def get_my_week_question_set() -> tuple[Response, int]:
	"""Fetch or create the question set for the mentor's currently active assignment or draft workspace."""
	mentor_id: int = int(get_jwt_identity())

	with get_db_session() as session:
		q_set = _get_or_create_active_question_set(session, mentor_id, auto_create_draft=True)
		if not q_set:
			return api_success(
				None,
				message="No active or upcoming mentor rotation found for you.",
			)
		return api_success(serialize_question_set(q_set))


# ========================================================
# MCQ Question Management (Create, Edit, Delete, Bulk Import)
# ========================================================


@mentor_bp.route("/questions/mcq", methods=["POST"], strict_slashes=False)
@mentor_bp.route("/mcq/create", methods=["POST"], strict_slashes=False)
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def add_mcq() -> tuple[Response, int]:
	"""Add an MCQ to the active question set."""
	mentor_id: int = int(get_jwt_identity())
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data:
		return api_error("INVALID_PAYLOAD", "Request body must be valid JSON.")

	prompt_text: str = str(data.get("prompt_text", "")).strip()
	options: list[str] = data.get("options", [])
	correct_index: int | None = data.get("correct_option_index")
	explanation: str | None = data.get("explanation")
	difficulty_str: str = str(data.get("difficulty", "medium")).lower()

	if not prompt_text or len(options) < 2 or correct_index is None:
		return api_error(
			"MISSING_FIELDS",
			"'prompt_text', 'options' (>=2), and 'correct_option_index' are required.",
		)

	if correct_index < 0 or correct_index >= len(options):
		return api_error("INVALID_INDEX", "correct_option_index is out of range.")

	safe_prompt: str = sanitize_text(prompt_text, max_length=4096, allow_html=True)
	safe_explanation: str | None = (
		sanitize_text(explanation, max_length=4096, allow_html=True) if explanation else None
	)
	safe_options: list[str] = [sanitize_text(opt, max_length=1024) for opt in options]

	with get_db_session() as session:
		question_set_id: int | None = data.get("question_set_id")
		if question_set_id:
			q_set = session.get(QuestionSet, question_set_id)
		else:
			q_set = _get_or_create_active_question_set(session, mentor_id)

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

		return api_success(serialize_question_set(q_set), message="MCQ added successfully.")


@mentor_bp.route("/questions/mcq/<int:mcq_id>", methods=["PUT"], strict_slashes=False)
@mentor_bp.route("/mcq/<int:mcq_id>", methods=["PUT"], strict_slashes=False)
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def update_mcq(mcq_id: int) -> tuple[Response, int]:
	"""Edit an existing MCQ in draft status."""
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data:
		return api_error("INVALID_PAYLOAD", "Request body must be valid JSON.")

	with get_db_session() as session:
		mcq: MCQQuestion | None = session.get(MCQQuestion, mcq_id)
		if not mcq:
			return api_error("NOT_FOUND", "MCQ not found.", status_code=404)

		if mcq.question_set.status != QuestionSetStatus.DRAFT:
			return api_error("LOCKED", "Cannot edit questions in a published question set.", status_code=400)

		if "prompt_text" in data and str(data["prompt_text"]).strip():
			mcq.prompt_text = sanitize_text(str(data["prompt_text"]), max_length=4096, allow_html=True)

		if "options" in data and isinstance(data["options"], list) and len(data["options"]) >= 2:
			mcq.options = [sanitize_text(str(opt), max_length=1024) for opt in data["options"]]

		if "correct_option_index" in data:
			idx = int(data["correct_option_index"])
			if 0 <= idx < len(mcq.options):
				mcq.correct_option_index = idx

		if "explanation" in data:
			mcq.explanation = (
				sanitize_text(str(data["explanation"]), max_length=4096, allow_html=True)
				if data["explanation"]
				else None
			)

		if "difficulty" in data:
			diff = str(data["difficulty"]).lower()
			if diff in DifficultyLevel.__members__.values():
				mcq.difficulty = DifficultyLevel(diff)

		session.flush()
		return api_success(serialize_question_set(mcq.question_set), message="MCQ updated successfully.")


@mentor_bp.route("/questions/mcq/<int:mcq_id>", methods=["DELETE"], strict_slashes=False)
@mentor_bp.route("/mcq/<int:mcq_id>", methods=["DELETE"], strict_slashes=False)
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def delete_mcq(mcq_id: int) -> tuple[Response, int]:
	"""Delete an MCQ from draft status."""
	with get_db_session() as session:
		mcq: MCQQuestion | None = session.get(MCQQuestion, mcq_id)
		if not mcq:
			return api_error("NOT_FOUND", "MCQ not found.", status_code=404)

		if mcq.question_set.status != QuestionSetStatus.DRAFT:
			return api_error("LOCKED", "Cannot delete questions from a published set.", status_code=400)

		q_set = mcq.question_set
		session.delete(mcq)
		session.flush()

		return api_success(serialize_question_set(q_set), message="MCQ removed from question pool.")


@mentor_bp.route("/questions/import-mcq-sheet", methods=["POST"], strict_slashes=False)
@mentor_bp.route("/mcq/import-sheet", methods=["POST"], strict_slashes=False)
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def import_mcq_sheet() -> tuple[Response, int]:
	"""Bulk import MCQs from an Excel or CSV file via AI extraction."""
	mentor_id: int = int(get_jwt_identity())
	if "file" not in request.files:
		return api_error("MISSING_FILE", "Spreadsheet file is required.")

	file = request.files["file"]
	filename: str = file.filename or ""
	ext: str = os.path.splitext(filename)[1].lower()

	if ext not in (".xlsx", ".csv"):
		return api_error("UNSUPPORTED_FORMAT", "Only .xlsx and .csv files are supported.")

	content: bytes = file.read()
	if len(content) > 10 * 1024 * 1024:
		return api_error("FILE_TOO_LARGE", "File size exceeds 10MB limit.")

	# Extract rows
	sample_grid: list[list[str]] = []
	try:
		if ext == ".xlsx":
			wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
			sheet = wb.active
			if sheet:
				for excel_row in sheet.iter_rows(values_only=True):
					row_str = [str(cell).strip() if cell is not None else "" for cell in excel_row]
					if any(row_str):
						sample_grid.append(row_str)
		else:
			decoded = content.decode("utf-8", errors="replace")
			reader = csv.reader(io.StringIO(decoded))
			for csv_row in reader:
				row_str = [str(cell).strip() for cell in csv_row]
				if any(row_str):
					sample_grid.append(row_str)
	except Exception as exc:
		return api_error("PARSING_ERROR", f"Could not read spreadsheet: {exc}")

	if not sample_grid:
		return api_error("EMPTY_FILE", "Uploaded sheet is empty.")

	# Parse via AI service
	extracted_questions: list[Any] = []
	try:
		parse_res = ai_service.parse_mcq_sheet(sample_grid[:50])
		extracted_questions = list(parse_res.questions)
	except Exception:
		# Fallback heuristic: assume Row format: [Question, OptA, OptB, OptC, OptD, Answer, Explanation, Difficulty]
		start_idx = 1 if any("question" in cell.lower() or "prompt" in cell.lower() for cell in sample_grid[0]) else 0
		for grid_row in sample_grid[start_idx:]:
			if len(grid_row) >= 5 and grid_row[0].strip():
				opts = [grid_row[i].strip() for i in range(1, min(5, len(grid_row))) if grid_row[i].strip()]
				if len(opts) >= 2:
					ans_idx = 0
					if len(grid_row) > 5 and grid_row[5].strip():
						ans_val = grid_row[5].strip().upper()
						if ans_val in ("A", "B", "C", "D"):
							ans_idx = ord(ans_val) - ord("A")
						elif ans_val.isdigit():
							ans_idx = max(0, min(int(ans_val), len(opts) - 1))
					exp = grid_row[6].strip() if len(grid_row) > 6 else None
					diff_str = grid_row[7].strip().lower() if len(grid_row) > 7 else "medium"
					extracted_questions.append(
						type("ParsedItem", (), {
							"prompt_text": grid_row[0].strip(),
							"options": opts,
							"correct_option_index": ans_idx,
							"explanation": exp,
							"difficulty": diff_str,
						})()
					)

	if not extracted_questions:
		return api_error("NO_QUESTIONS_FOUND", "No valid MCQs could be extracted from this spreadsheet.")

	with get_db_session() as session:
		q_set_id = request.form.get("question_set_id")
		if q_set_id and str(q_set_id).isdigit():
			q_set = session.get(QuestionSet, int(q_set_id))
		else:
			q_set = _get_or_create_active_question_set(session, mentor_id, auto_create_draft=True)

		if not q_set or q_set.status != QuestionSetStatus.DRAFT:
			return api_error("INVALID_QUESTION_SET", "Question set must be in draft status.", status_code=400)

		added_count = 0
		for item in extracted_questions:
			safe_prompt = sanitize_text(item.prompt_text, max_length=4096, allow_html=True)
			safe_opts = [sanitize_text(o, max_length=1024) for o in item.options]
			safe_exp = sanitize_text(item.explanation, max_length=4096, allow_html=True) if item.explanation else None
			c_idx = max(0, min(item.correct_option_index, len(safe_opts) - 1))

			mcq = MCQQuestion(
				question_set_id=q_set.id,
				prompt_text=safe_prompt,
				options=safe_opts,
				correct_option_index=c_idx,
				explanation=safe_exp,
				difficulty=DifficultyLevel(item.difficulty)
				if item.difficulty in DifficultyLevel.__members__.values()
				else DifficultyLevel.MEDIUM,
			)
			session.add(mcq)
			added_count += 1

		session.flush()
		return api_success(
			serialize_question_set(q_set),
			message=f"Successfully imported {added_count} MCQs into your question pool.",
		)


# ========================================================
# Coding Question Management (Create, Edit, Delete, Bulk Import)
# ========================================================


@mentor_bp.route("/questions/coding", methods=["POST"], strict_slashes=False)
@mentor_bp.route("/coding/create", methods=["POST"], strict_slashes=False)
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def add_coding_question() -> tuple[Response, int]:
	"""Add a coding question with exactly 3 sample cases and 10 hidden test cases separated."""
	mentor_id: int = int(get_jwt_identity())
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data:
		return api_error("INVALID_PAYLOAD", "Request body must be valid JSON.")

	title: str = str(data.get("title", "")).strip()
	word_problem: str = str(data.get("word_problem_text", "")).strip()
	constraints: str = str(data.get("constraints_text", "")).strip()
	difficulty_str: str = str(data.get("difficulty", "medium")).lower()

	# Optional test cases in the JSON payload (empty lists allowed in draft)
	raw_sample = data.get("sample_test_cases", [])
	raw_hidden = data.get("hidden_test_cases", [])
	if not isinstance(raw_sample, list) or not isinstance(raw_hidden, list):
		return api_error(
			"INVALID_TEST_CASES",
			"'sample_test_cases' and 'hidden_test_cases' must be provided as lists.",
		)

	# Collect valid non-empty test cases; empty ones are ignored/omitted
	sample_cases = [
		tc for tc in raw_sample
		if str(tc.get("input", tc.get("input_data", ""))).strip() and str(tc.get("expected_output", "")).strip()
	]
	hidden_cases = [
		tc for tc in raw_hidden
		if str(tc.get("input", tc.get("input_data", ""))).strip() and str(tc.get("expected_output", "")).strip()
	]

	if not title or not word_problem:
		return api_error("MISSING_FIELDS", "'title' and 'word_problem_text' are required.")

	safe_title: str = sanitize_text(title, max_length=255)
	safe_problem: str = sanitize_text(word_problem, max_length=16384, allow_html=True)
	safe_constraints: str = sanitize_text(constraints, max_length=4096, allow_html=True)

	with get_db_session() as session:
		question_set_id: int | None = data.get("question_set_id")
		if question_set_id:
			q_set = session.get(QuestionSet, question_set_id)
		else:
			q_set = _get_or_create_active_question_set(session, mentor_id)

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
			difficulty=DifficultyLevel(difficulty_str)
			if difficulty_str in DifficultyLevel.__members__.values()
			else DifficultyLevel.MEDIUM,
			function_name=str(data.get("function_name", "solve")).strip() or "solve",
			parameter_definitions=data.get("parameter_definitions", []) if isinstance(data.get("parameter_definitions"), list) else [],
			return_type=str(data.get("return_type", "int")).strip() or "int",
			starter_templates=data.get("starter_templates", {}) if isinstance(data.get("starter_templates"), dict) else {},
		)
		session.add(coding_q)
		session.flush()

		for tc in sample_cases:
			coding_q.sample_test_cases.append(
				CodingSampleTestCase(
					coding_question_id=coding_q.id,
					input_data=str(tc.get("input", tc.get("input_data", ""))).strip(),
					expected_output=str(tc.get("expected_output", "")).strip(),
				)
			)

		for tc in hidden_cases:
			coding_q.hidden_test_cases.append(
				CodingHiddenTestCase(
					coding_question_id=coding_q.id,
					input_data=str(tc.get("input", tc.get("input_data", ""))).strip(),
					expected_output=str(tc.get("expected_output", "")).strip(),
				)
			)

		session.flush()
		session.refresh(coding_q)
		session.refresh(q_set)
		return api_success(
			serialize_question_set(q_set),
			message=f"Coding question created with {len(sample_cases)} sample cases and {len(hidden_cases)} hidden test cases.",
		)


@mentor_bp.route("/questions/coding/<int:coding_q_id>", methods=["PUT"], strict_slashes=False)
@mentor_bp.route("/coding/<int:coding_q_id>", methods=["PUT"], strict_slashes=False)
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def update_coding_question(coding_q_id: int) -> tuple[Response, int]:
	"""Edit an existing coding problem and its test cases."""
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data:
		return api_error("INVALID_PAYLOAD", "Request body must be valid JSON.")

	with get_db_session() as session:
		coding_q: CodingQuestion | None = session.get(CodingQuestion, coding_q_id)
		if not coding_q:
			return api_error("NOT_FOUND", "Coding question not found.", status_code=404)

		if coding_q.question_set.status != QuestionSetStatus.DRAFT:
			return api_error("LOCKED", "Cannot edit questions in a published set.", status_code=400)

		if "title" in data and str(data["title"]).strip():
			coding_q.title = sanitize_text(str(data["title"]), max_length=255)

		if "word_problem_text" in data and str(data["word_problem_text"]).strip():
			coding_q.word_problem_text = sanitize_text(str(data["word_problem_text"]), max_length=16384, allow_html=True)

		if "constraints_text" in data:
			coding_q.constraints_text = sanitize_text(str(data["constraints_text"]), max_length=4096, allow_html=True)

		if "difficulty" in data:
			diff = str(data["difficulty"]).lower()
			if diff in DifficultyLevel.__members__.values():
				coding_q.difficulty = DifficultyLevel(diff)

		if "function_name" in data:
			coding_q.function_name = str(data["function_name"]).strip() or "solve"

		if "parameter_definitions" in data and isinstance(data["parameter_definitions"], list):
			coding_q.parameter_definitions = data["parameter_definitions"]

		if "return_type" in data:
			coding_q.return_type = str(data["return_type"]).strip() or "int"

		if "starter_templates" in data and isinstance(data["starter_templates"], dict):
			coding_q.starter_templates = data["starter_templates"]

		# Replace test cases if provided
		raw_sample = data.get("sample_test_cases")
		raw_hidden = data.get("hidden_test_cases")

		if raw_sample is not None or raw_hidden is not None:
			if (raw_sample is not None and not isinstance(raw_sample, list)) or (
				raw_hidden is not None and not isinstance(raw_hidden, list)
			):
				return api_error(
					"INVALID_TEST_CASES",
					"'sample_test_cases' and 'hidden_test_cases' must be provided as lists.",
				)
			sample_cases = [
				tc for tc in (raw_sample or [])
				if str(tc.get("input", tc.get("input_data", ""))).strip() and str(tc.get("expected_output", "")).strip()
			]
			hidden_cases = [
				tc for tc in (raw_hidden or [])
				if str(tc.get("input", tc.get("input_data", ""))).strip() and str(tc.get("expected_output", "")).strip()
			]

			# Remove old test cases from both tables and legacy
			coding_q.sample_test_cases.clear()
			coding_q.hidden_test_cases.clear()
			coding_q.legacy_test_cases.clear()
			session.flush()

			for tc in sample_cases:
				coding_q.sample_test_cases.append(
					CodingSampleTestCase(
						coding_question_id=coding_q.id,
						input_data=str(tc.get("input", tc.get("input_data", ""))).strip(),
						expected_output=str(tc.get("expected_output", "")).strip(),
					)
				)

			for tc in hidden_cases:
				coding_q.hidden_test_cases.append(
					CodingHiddenTestCase(
						coding_question_id=coding_q.id,
						input_data=str(tc.get("input", tc.get("input_data", ""))).strip(),
						expected_output=str(tc.get("expected_output", "")).strip(),
					)
				)

		session.flush()
		session.refresh(coding_q)
		session.refresh(coding_q.question_set)
		return api_success(serialize_question_set(coding_q.question_set), message="Coding problem updated.")


@mentor_bp.route("/questions/coding/<int:coding_q_id>", methods=["DELETE"], strict_slashes=False)
@mentor_bp.route("/coding/<int:coding_q_id>", methods=["DELETE"], strict_slashes=False)
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def delete_coding_question(coding_q_id: int) -> tuple[Response, int]:
	"""Delete a coding question from draft status."""
	with get_db_session() as session:
		coding_q: CodingQuestion | None = session.get(CodingQuestion, coding_q_id)
		if not coding_q:
			return api_error("NOT_FOUND", "Coding question not found.", status_code=404)

		if coding_q.question_set.status != QuestionSetStatus.DRAFT:
			return api_error("LOCKED", "Cannot delete questions from a published set.", status_code=400)

		q_set = coding_q.question_set
		session.delete(coding_q)
		session.flush()

		return api_success(serialize_question_set(q_set), message="Coding problem removed from question pool.")


@mentor_bp.route("/questions/import-coding-sheet", methods=["POST"], strict_slashes=False)
@mentor_bp.route("/coding/import-sheet", methods=["POST"], strict_slashes=False)
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def import_coding_sheet() -> tuple[Response, int]:
	"""Bulk import coding challenges from an Excel or CSV file with automatic AI test case synthesis."""
	mentor_id: int = int(get_jwt_identity())
	if "file" not in request.files:
		return api_error("MISSING_FILE", "Spreadsheet file is required.")

	file = request.files["file"]
	filename: str = file.filename or ""
	ext: str = os.path.splitext(filename)[1].lower()

	if ext not in (".xlsx", ".csv"):
		return api_error("UNSUPPORTED_FORMAT", "Only .xlsx and .csv files are supported.")

	content: bytes = file.read()
	if len(content) > 10 * 1024 * 1024:
		return api_error("FILE_TOO_LARGE", "File size exceeds 10MB limit.")

	sample_grid: list[list[str]] = []
	try:
		if ext == ".xlsx":
			wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
			sheet = wb.active
			if sheet:
				for excel_row in sheet.iter_rows(values_only=True):
					row_str = [str(cell).strip() if cell is not None else "" for cell in excel_row]
					if any(row_str):
						sample_grid.append(row_str)
		else:
			decoded = content.decode("utf-8", errors="replace")
			reader = csv.reader(io.StringIO(decoded))
			for csv_row in reader:
				row_str = [str(cell).strip() for cell in csv_row]
				if any(row_str):
					sample_grid.append(row_str)
	except Exception as exc:
		return api_error("PARSING_ERROR", f"Could not read spreadsheet: {exc}")

	if not sample_grid:
		return api_error("EMPTY_FILE", "Uploaded sheet is empty.")

	# Extract coding problems from the spreadsheet
	extracted_problems: list[Any] = []
	header_row = [c.lower() for c in sample_grid[0]] if sample_grid else []
	has_title_header = any("title" in h or "problem" in h for h in header_row)

	# Direct column extraction when sheet has standard table structure
	start_idx = 1 if has_title_header else 0
	for grid_row in sample_grid[start_idx:]:
		if len(grid_row) >= 2 and grid_row[0].strip() and grid_row[1].strip():
			title = grid_row[0].strip()
			desc = grid_row[1].strip()
			constraints = grid_row[2].strip() if len(grid_row) > 2 and grid_row[2].strip() else "1 <= N <= 10^5\nAll values within signed 32-bit integer limits."
			diff_str = grid_row[3].strip().lower() if len(grid_row) > 3 else "medium"

			sample_tcs: list[TestCaseModel] = []
			hidden_tcs: list[TestCaseModel] = []

			# Extract test case pairs from columns
			for c in range(4, len(grid_row) - 1, 2):
				in_val = grid_row[c].strip()
				out_val = grid_row[c + 1].strip()
				if in_val or out_val:
					col_header = header_row[c] if c < len(header_row) else ""
					if "hidden" in col_header:
						hidden_tcs.append(TestCaseModel(input_data=in_val, expected_output=out_val))
					else:
						sample_tcs.append(TestCaseModel(input_data=in_val, expected_output=out_val))

			extracted_problems.append(
				type("ParsedCoding", (), {
					"title": title,
					"word_problem_text": desc,
					"constraints_text": constraints,
					"difficulty": diff_str,
					"sample_test_cases": sample_tcs,
					"hidden_test_cases": hidden_tcs,
				})()
			)

	if not extracted_problems:
		try:
			parse_res = ai_service.parse_coding_sheet(sample_grid[:35])
			extracted_problems = list(parse_res.questions)
		except Exception as exc:
			logger.warning("AI parse_coding_sheet failed: %s", str(exc))

	if not extracted_problems:
		return api_error("NO_PROBLEMS_FOUND", "No valid coding challenges could be extracted from this spreadsheet.")

	with get_db_session() as session:
		q_set_id = request.form.get("question_set_id")
		if q_set_id and str(q_set_id).isdigit():
			q_set = session.get(QuestionSet, int(q_set_id))
		else:
			q_set = _get_or_create_active_question_set(session, mentor_id, auto_create_draft=True)

		if not q_set or q_set.status != QuestionSetStatus.DRAFT:
			return api_error("INVALID_QUESTION_SET", "Question set must be in draft status.", status_code=400)

		added_count = 0
		for prob in extracted_problems:
			safe_title = sanitize_text(prob.title, max_length=255)
			safe_prob = sanitize_text(prob.word_problem_text, max_length=16384, allow_html=True)
			safe_const = sanitize_text(prob.constraints_text, max_length=4096, allow_html=True)

			coding_q = CodingQuestion(
				question_set_id=q_set.id,
				title=safe_title,
				word_problem_text=safe_prob,
				constraints_text=safe_const,
				difficulty=DifficultyLevel(prob.difficulty)
				if prob.difficulty in DifficultyLevel.__members__.values()
				else DifficultyLevel.MEDIUM,
			)
			session.add(coding_q)
			session.flush()

			sample_cases: list[dict[str, str]] = [
				{"input_data": tc.input_data, "expected_output": tc.expected_output}
				for tc in getattr(prob, "sample_test_cases", [])
				if tc.input_data or tc.expected_output
			]
			hidden_cases: list[dict[str, str]] = [
				{"input_data": tc.input_data, "expected_output": tc.expected_output}
				for tc in getattr(prob, "hidden_test_cases", [])
				if tc.input_data or tc.expected_output
			]

			# If fewer than 3 samples or fewer than 10 hidden cases, use AI to generate the missing cases
			if len(sample_cases) < 3 or len(hidden_cases) < 10:
				try:
					ai_res = ai_service.generate_full_test_suite(
						title=safe_title,
						problem_text=safe_prob,
						constraints_text=safe_const,
						existing_samples=sample_cases,
						existing_hiddens=hidden_cases,
					)
					ai_samples = [
						{"input_data": tc.input_data.strip(), "expected_output": tc.expected_output.strip()}
						for tc in ai_res.sample_test_cases
						if tc.input_data.strip() and tc.expected_output.strip()
					]
					ai_hiddens = [
						{"input_data": tc.input_data.strip(), "expected_output": tc.expected_output.strip()}
						for tc in ai_res.hidden_test_cases
						if tc.input_data.strip() and tc.expected_output.strip()
					]
					if ai_samples:
						sample_cases = ai_samples
					if ai_hiddens:
						hidden_cases = ai_hiddens
				except Exception as e:
					logger.warning("AI test generation failed for '%s': %s", safe_title, str(e))
					# Strictly NO fallback! If AI fails, missing test cases are left empty.

				time.sleep(1.0)

			for tc in sample_cases:
				in_d = tc.get("input_data", "").strip()
				exp_o = tc.get("expected_output", "").strip()
				if in_d and exp_o:
					coding_q.sample_test_cases.append(
						CodingSampleTestCase(
							coding_question_id=coding_q.id,
							input_data=in_d,
							expected_output=exp_o,
						)
					)

			for tc in hidden_cases:
				in_d = tc.get("input_data", "").strip()
				exp_o = tc.get("expected_output", "").strip()
				if in_d and exp_o:
					coding_q.hidden_test_cases.append(
						CodingHiddenTestCase(
							coding_question_id=coding_q.id,
							input_data=in_d,
							expected_output=exp_o,
						)
					)

			added_count += 1

		session.flush()
		session.refresh(q_set)
		return api_success(
			serialize_question_set(q_set),
			message=f"Successfully imported {added_count} coding challenges into question pool.",
		)


# ========================================================
# AI Test Case Generation & Append
# ========================================================


@mentor_bp.route("/coding/<int:coding_id>/generate-ai-tests", methods=["POST"], strict_slashes=False)
@mentor_bp.route("/questions/coding/ai-generate-tests", methods=["POST"], strict_slashes=False)
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def generate_ai_stress_tests(coding_id: int | None = None) -> tuple[Response, int]:
	"""Generate 3 sample cases and 10 hidden test cases separated in JSON using AI."""
	raw_json = request.get_json(silent=True)
	data: dict[str, Any] = raw_json if isinstance(raw_json, dict) else {}

	with get_db_session() as session:
		title: str = str(data.get("title", ""))
		problem: str = str(data.get("word_problem_text", ""))
		constraints: str = str(data.get("constraints_text", ""))

		if coding_id:
			coding_q = session.get(CodingQuestion, coding_id)
			if coding_q:
				title = title or coding_q.title
				problem = problem or coding_q.word_problem_text
				constraints = constraints or coding_q.constraints_text

		existing_samples: list[dict[str, str]] = []
		existing_hiddens: list[dict[str, str]] = []

		if coding_id:
			coding_q = session.get(CodingQuestion, coding_id)
			if coding_q:
				title = title or coding_q.title
				problem = problem or coding_q.word_problem_text
				constraints = constraints or coding_q.constraints_text
				existing_samples = [
					{"input_data": s.input_data, "expected_output": s.expected_output}
					for s in coding_q.sample_test_cases
				]
				existing_hiddens = [
					{"input_data": h.input_data, "expected_output": h.expected_output}
					for h in coding_q.hidden_test_cases
				]

		if not title or not problem:
			return api_error("MISSING_FIELDS", "'title' and 'word_problem_text' are required.")

		try:
			full_res = ai_service.generate_full_test_suite(
				title=title,
				problem_text=problem,
				constraints_text=constraints,
				reference_solution=data.get("reference_solution"),
				existing_samples=existing_samples,
				existing_hiddens=existing_hiddens,
			)
			sample_cases = [
				{"input": tc.input_data.strip(), "expected_output": tc.expected_output.strip()}
				for tc in full_res.sample_test_cases
				if tc.input_data.strip() and tc.expected_output.strip()
			]
			hidden_cases = [
				{"input": tc.input_data.strip(), "expected_output": tc.expected_output.strip()}
				for tc in full_res.hidden_test_cases
				if tc.input_data.strip() and tc.expected_output.strip()
			]

			return api_success(
				{
					"sample_test_cases": sample_cases,
					"hidden_test_cases": hidden_cases,
				}
			)
		except Exception as e:
			logger.warning("AI generate_full_test_suite failed: %s", str(e))
			return api_error(
				"AI_GENERATION_FAILED",
				f"AI test case generation failed: {e}. Missing test cases left empty.",
				status_code=500,
			)


@mentor_bp.route("/coding/<int:coding_id>/append-test-cases", methods=["POST"], strict_slashes=False)
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def append_test_cases(coding_id: int) -> tuple[Response, int]:
	"""Append accepted AI test cases to a coding question's hidden test cases."""
	data: dict[str, Any] | None = request.get_json(silent=True)
	test_cases: list[dict[str, Any]] = data.get("test_cases", []) if data else []

	if not test_cases:
		return api_error("MISSING_CASES", "No test cases provided.")

	with get_db_session() as session:
		coding_q = session.get(CodingQuestion, coding_id)
		if not coding_q:
			return api_error("NOT_FOUND", "Coding question not found.", status_code=404)

		if coding_q.question_set.status != QuestionSetStatus.DRAFT:
			return api_error("LOCKED", "Cannot modify test cases in a published set.", status_code=400)

		for tc in test_cases:
			in_data = str(tc.get("input", tc.get("input_data", ""))).strip()
			exp_out = str(tc.get("expected_output", "")).strip()
			if in_data and exp_out:
				coding_q.hidden_test_cases.append(
					CodingHiddenTestCase(
						coding_question_id=coding_q.id,
						input_data=in_data,
						expected_output=exp_out,
					)
				)

		session.flush()
		session.refresh(coding_q)
		session.refresh(coding_q.question_set)
		return api_success(
			serialize_question_set(coding_q.question_set),
			message=f"Appended {len(test_cases)} hidden test cases.",
		)


# ========================================================
# Question Set Publishing & Integrity Checks
# ========================================================


@mentor_bp.route("/question-set/publish", methods=["POST"], strict_slashes=False)
@mentor_bp.route("/question-set/<int:question_set_id>/publish", methods=["POST"], strict_slashes=False)
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def publish_question_set(question_set_id: int | None = None) -> tuple[Response, int]:
	"""Publish question set after verifying pool size minimums and test case completeness."""
	data: dict[str, Any] | None = request.get_json(silent=True)
	target_id: int | None = question_set_id or (data.get("question_set_id") if data else None)

	with get_db_session() as session:
		if not target_id:
			mentor_id = int(get_jwt_identity())
			q_set = _get_or_create_active_question_set(session, mentor_id)
		else:
			q_set = session.get(QuestionSet, target_id)

		if not q_set:
			return api_error("NOT_FOUND", "Question set not found.", status_code=404)

		if not q_set.mentor_assignment_id:
			return api_error(
				"NO_ROTATION_ASSIGNED",
				"Cannot publish yet: You have not been assigned to a mentor rotation schedule by an admin. Your questions are saved in Draft status and will be ready to publish as soon as a schedule is assigned.",
				status_code=400,
			)

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

		# Verify all coding questions have full verified test cases (3 sample, 10 hidden)
		incomplete_questions: list[str] = [
			f"'{q.title}' ({len(q.sample_test_cases)}/3 sample, {len(q.hidden_test_cases)}/10 hidden)"
			for q in q_set.coding_questions
			if len(q.sample_test_cases) < 3 or len(q.hidden_test_cases) < 10
		]
		if incomplete_questions:
			return api_error(
				"INCOMPLETE_TEST_CASES",
				f"Cannot publish: All coding questions require at least 3 sample test cases and 10 hidden test cases. Incomplete questions: {', '.join(incomplete_questions)}.",
				status_code=400,
			)

		q_set.status = QuestionSetStatus.PUBLISHED
		session.flush()
		return api_success(serialize_question_set(q_set), message="Question set published successfully.")


# ========================================================
# Flagged Submissions Review
# ========================================================


@mentor_bp.route("/flagged-submissions", methods=["GET"], strict_slashes=False)
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


@mentor_bp.route("/flagged-submissions/<int:submission_id>/review", methods=["POST"], strict_slashes=False)
@mentor_bp.route("/flagged-submissions/<int:submission_id>/resolve", methods=["POST"], strict_slashes=False)
@jwt_required()
@require_roles(UserRole.MENTOR, UserRole.ADMIN)
def review_flagged_submission(submission_id: int) -> tuple[Response, int]:
	"""Mentor or Admin human review of a flagged submission."""
	raw_json = request.get_json(silent=True)
	data: dict[str, Any] = raw_json if isinstance(raw_json, dict) else {}
	decision: str = str(data.get("decision") or data.get("resolution") or "").lower()
	notes: str = str(data.get("notes", ""))

	if decision in ("clean", "dismiss"):
		status = AIReviewStatus.CLEAN
	elif decision in ("penalize", "action"):
		status = AIReviewStatus.FLAGGED
	else:
		return api_error("INVALID_DECISION", "Decision must be 'clean', 'dismiss', 'penalize', or 'action'.")

	with get_db_session() as session:
		sub: CodeSubmission | None = session.get(CodeSubmission, submission_id)
		if not sub:
			return api_error("NOT_FOUND", "Submission not found.", status_code=404)

		sub.ai_review_status = status
		sub.ai_review_notes = notes
		session.flush()
		return api_success(sub.to_dict(), message="Submission review updated.")
