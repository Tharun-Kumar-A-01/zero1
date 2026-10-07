from __future__ import annotations

import contextlib
import csv
import io
import os
import tempfile
from datetime import UTC, date, datetime
from typing import Any

import openpyxl
from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import select

from app.api.utils import api_error, api_success, require_roles
from app.database import get_db_session
from app.models.enums import AssignmentStatus, ImportJobStatus, QuestionSetStatus, UserRole
from app.models.import_job import ImportJob
from app.models.mentor import CustomLeave, MentorAssignment
from app.models.question import QuestionSet
from app.models.user import User
from app.services.ai_client import ExcelMappingResult, ai_service
from app.services.sanitizer import sanitize_text

admin_bp: Blueprint = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/students/import", methods=["POST"])
@admin_bp.route("/students/import-upload", methods=["POST"])
@jwt_required()
@require_roles(UserRole.ADMIN)
def upload_student_roster() -> tuple[Response, int]:
	"""Upload Excel or CSV roster, extract sample grid, and infer mapping via AI."""
	admin_id: int = int(get_jwt_identity())

	if "file" not in request.files:
		return api_error("NO_FILE", "Please upload a file with key 'file'.")

	file = request.files["file"]
	filename: str = file.filename or ""
	ext: str = os.path.splitext(filename)[1].lower()

	if ext not in (".xlsx", ".csv"):
		return api_error(
			"UNSUPPORTED_FORMAT",
			"Only .xlsx and .csv files are supported. Macro files (.xlsm) are prohibited.",
		)

	target_year: str = (
		request.form.get("target_year_batch") or request.form.get("year_batch") or ""
	).strip()
	if not target_year:
		return api_error("MISSING_YEAR", "'target_year_batch' (e.g. '2026') is required.")

	content: bytes = file.read()
	if len(content) > 10 * 1024 * 1024:  # 10MB limit
		return api_error("FILE_TOO_LARGE", "File size exceeds 10MB limit.")

	# Extract sample grid
	sample_grid: list[list[str]] = []
	try:
		if ext == ".xlsx":
			wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
			sheet = wb.active
			if sheet is None:
				return api_error("INVALID_FILE", "Workbook has no active sheet.")
			for row in sheet.iter_rows(max_row=25, values_only=True):
				row_str: list[str] = [str(cell).strip() if cell is not None else "" for cell in row]
				sample_grid.append(row_str)
		else:
			decoded: str = content.decode("utf-8", errors="replace")
			reader = csv.reader(io.StringIO(decoded))
			for i, csv_row in enumerate(reader):
				if i >= 25:
					break
				sample_grid.append([str(cell).strip() for cell in csv_row])
	except Exception as exc:
		return api_error("PARSING_ERROR", f"Could not parse sheet: {exc}")

	if not sample_grid:
		return api_error("EMPTY_FILE", "Uploaded sheet is empty.")

	# Call AI for mapping inference
	try:
		inferred_mapping: ExcelMappingResult = ai_service.infer_excel_mapping(sample_grid)
	except Exception:
		# Fallback standard default mapping if AI is unreachable
		inferred_mapping = ExcelMappingResult(
			header_row_index=0,
			data_row_start_index=1,
			column_mapping={"name": 0, "roll_number": 1, "email": 2},
			confidence=0.5,
		)

	# Save uploaded file to persistent storage path for this import job
	import_dir = os.path.join(tempfile.gettempdir(), "zero1_imports")
	os.makedirs(import_dir, exist_ok=True)
	safe_fname = "".join(c for c in filename if c.isalnum() or c in "._-") or "roster.xlsx"
	saved_filename = f"roster_{admin_id}_{int(datetime.now(UTC).timestamp())}_{safe_fname}"
	saved_path = os.path.join(import_dir, saved_filename)
	with open(saved_path, "wb") as f_out:
		f_out.write(content)

	# Store import job record
	with get_db_session() as session:
		job = ImportJob(
			admin_id=admin_id,
			original_filename=sanitize_text(filename, max_length=255),
			storage_path=saved_path,
			status=ImportJobStatus.AWAITING_CONFIRMATION,
			target_year_batch=sanitize_text(target_year, max_length=32),
			ai_parse_result=inferred_mapping.model_dump(),
		)
		session.add(job)
		session.flush()

		return api_success(
			{
				"job_id": job.id,
				"sample_grid": sample_grid,
				"inferred_mapping": inferred_mapping.model_dump(),
			},
			message="Sheet parsed. Please review and confirm column mapping.",
		)


@admin_bp.route("/students/import/<int:job_id>/confirm", methods=["POST"])
@admin_bp.route("/students/import-commit", methods=["POST"])
@jwt_required()
@require_roles(UserRole.ADMIN)
def confirm_student_import(job_id: int | None = None) -> tuple[Response, int]:
	"""Admin confirms column mapping and commits imported students to database."""
	data: dict[str, Any] | None = request.get_json(silent=True)
	if job_id is None and data:
		job_id = int(data.get("job_id", 0))
	column_mapping: dict[str, int] = data.get("column_mapping", {}) if data else {}
	rows_data: list[list[str]] = data.get("rows", []) if data else []

	with get_db_session() as session:
		job: ImportJob | None = session.get(ImportJob, job_id) if job_id else None
		if not job or job.status != ImportJobStatus.AWAITING_CONFIRMATION:
			return api_error("INVALID_JOB", "Job not found or already processed.", status_code=400)

		# If rows not supplied in JSON, load all rows from stored spreadsheet file
		if not rows_data and job.storage_path and os.path.exists(job.storage_path):
			try:
				if job.storage_path.lower().endswith(".xlsx"):
					wb = openpyxl.load_workbook(job.storage_path, data_only=True, read_only=True)
					sheet = wb.active
					if sheet:
						for excel_row in sheet.iter_rows(values_only=True):
							row_str = [str(cell).strip() if cell is not None else "" for cell in excel_row]
							if any(row_str):
								rows_data.append(row_str)
				else:
					with open(job.storage_path, encoding="utf-8", errors="replace") as f_in:
						reader = csv.reader(f_in)
						for csv_row in reader:
							row_str = [str(cell).strip() for cell in csv_row]
							if any(row_str):
								rows_data.append(row_str)
			except Exception as exc:
				return api_error("FILE_READ_ERROR", f"Could not read stored import file: {exc}")

		if not rows_data:
			return api_error("NO_ROWS", "No student row data provided.")

		# Determine where data rows start (skip header row)
		start_row_idx = 1
		if job.ai_parse_result and isinstance(job.ai_parse_result, dict):
			start_row_idx = int(job.ai_parse_result.get("data_row_start_index", 1))

		data_rows = rows_data[start_row_idx:] if len(rows_data) > start_row_idx else rows_data

		name_col = column_mapping.get("name", 0)
		email_col = column_mapping.get("email", 1)
		roll_col = column_mapping.get("roll_number", 2)
		sec_col = column_mapping.get("section")

		imported_count: int = 0
		skipped_count: int = 0
		errors: list[str] = []

		for idx, row in enumerate(data_rows):
			if len(row) <= max(name_col, email_col, roll_col):
				skipped_count += 1
				continue

			name = sanitize_text(str(row[name_col] or ""), max_length=128)
			email = sanitize_text(str(row[email_col] or ""), max_length=255).lower()
			roll = sanitize_text(str(row[roll_col] or ""), max_length=64)
			section = (
				sanitize_text(str(row[sec_col] or ""), max_length=16)
				if sec_col is not None and len(row) > sec_col
				else None
			)

			if not name or not email or "@" not in email:
				skipped_count += 1
				continue

			# Check duplicate email
			existing = session.scalars(select(User).where(User.email == email)).first()
			if existing:
				errors.append(f"Row {idx + 1}: Email {email} already exists. Skipped.")
				skipped_count += 1
				continue

			student_user = User(
				name=name,
				email=email,
				role=UserRole.STUDENT,
				roll_number=roll,
				year_batch=job.target_year_batch,
				section=section,
			)
			student_user.set_password("StudentPassword@123")
			session.add(student_user)
			imported_count += 1

		job.status = ImportJobStatus.COMMITTED
		job.committed_at = datetime.now(UTC)
		job.error_log = "\n".join(errors) if errors else None

		# Clean up temporary file
		if job.storage_path and os.path.exists(job.storage_path):
			with contextlib.suppress(Exception):
				os.remove(job.storage_path)

		return api_success(
			{
				"imported_count": imported_count,
				"skipped_count": skipped_count,
				"errors": errors,
			},
			message=f"Import completed. {imported_count} students created.",
		)


@admin_bp.route("/mentors/rotation", methods=["POST"])
@admin_bp.route("/mentors/schedule", methods=["POST"])
@jwt_required()
@require_roles(UserRole.ADMIN)
def schedule_mentor_rotation() -> tuple[Response, int]:
	"""Assign a mentor to a designated week."""
	admin_id: int = int(get_jwt_identity())
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data:
		return api_error("INVALID_PAYLOAD", "Request body must be valid JSON.")

	user_id: int | None = data.get("user_id")
	start_str: str = str(data.get("week_start_date", ""))
	end_str: str = str(data.get("week_end_date", ""))

	if not user_id or not start_str or not end_str:
		return api_error(
			"MISSING_FIELDS", "'user_id', 'week_start_date', and 'week_end_date' are required."
		)

	try:
		week_start = date.fromisoformat(start_str)
		week_end = date.fromisoformat(end_str)
	except ValueError:
		return api_error("INVALID_DATE_FORMAT", "Dates must be ISO format (YYYY-MM-DD).")

	with get_db_session() as session:
		mentor_user = session.get(User, user_id)
		if not mentor_user:
			return api_error(
				"INVALID_MENTOR", "User must exist.", status_code=400
			)

		# Check date overlap
		stmt_overlap = select(MentorAssignment).where(
			MentorAssignment.status.in_([AssignmentStatus.ACTIVE, AssignmentStatus.UPCOMING]),
			MentorAssignment.week_start_date <= week_end,
			MentorAssignment.week_end_date >= week_start,
		)
		if session.scalars(stmt_overlap).first() is not None:
			return api_error(
				"OVERLAP_CONFLICT", "A mentor is already assigned for this date range."
			)

		assignment = MentorAssignment(
			user_id=user_id,
			week_start_date=week_start,
			week_end_date=week_end,
			status=AssignmentStatus.UPCOMING,
			created_by_admin_id=admin_id,
		)
		session.add(assignment)
		session.flush()

		# Auto-link any existing unassigned draft question set prepared by this mentor
		stmt_draft = (
			select(QuestionSet)
			.where(
				QuestionSet.mentor_id == user_id,
				QuestionSet.mentor_assignment_id.is_(None),
				QuestionSet.status == QuestionSetStatus.DRAFT,
			)
			.order_by(QuestionSet.id.desc())
		)
		draft_qs = session.scalars(stmt_draft).first()
		if draft_qs:
			draft_qs.mentor_assignment_id = assignment.id
			draft_qs.week_start_date = week_start
			session.flush()

		return api_success(assignment.to_dict(), message="Mentor rotation scheduled.")


@admin_bp.route("/mentors/rotation", methods=["GET"])
@jwt_required()
@require_roles(UserRole.ADMIN)
def get_rotation_schedule() -> tuple[Response, int]:
	"""List all scheduled mentor rotations."""
	with get_db_session() as session:
		stmt = select(MentorAssignment).order_by(MentorAssignment.week_start_date.desc())
		assignments = session.scalars(stmt).all()
		return api_success([a.to_dict() for a in assignments])


@admin_bp.route("/mentors/rotation/<int:rotation_id>", methods=["PUT"], strict_slashes=False)
@jwt_required()
@require_roles(UserRole.ADMIN)
def update_rotation(rotation_id: int) -> tuple[Response, int]:
	"""Update an existing mentor rotation (mentor and/or dates)."""
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data:
		return api_error("INVALID_PAYLOAD", "Request body must be valid JSON.")

	with get_db_session() as session:
		assignment = session.get(MentorAssignment, rotation_id)
		if not assignment:
			return api_error("NOT_FOUND", "Rotation not found.", status_code=404)

		if "user_id" in data:
			new_user_id = int(data["user_id"])
			if not session.get(User, new_user_id):
				return api_error("INVALID_MENTOR", "User not found.", status_code=400)
			assignment.user_id = new_user_id

		if "week_start_date" in data or "week_end_date" in data:
			try:
				new_start = date.fromisoformat(str(data.get("week_start_date", assignment.week_start_date)))
				new_end = date.fromisoformat(str(data.get("week_end_date", assignment.week_end_date)))
			except ValueError:
				return api_error("INVALID_DATE_FORMAT", "Dates must be ISO format (YYYY-MM-DD).")

			# Check overlap with other rotations (exclude self)
			stmt_overlap = select(MentorAssignment).where(
				MentorAssignment.id != rotation_id,
				MentorAssignment.status.in_([AssignmentStatus.ACTIVE, AssignmentStatus.UPCOMING]),
				MentorAssignment.week_start_date <= new_end,
				MentorAssignment.week_end_date >= new_start,
			)
			if session.scalars(stmt_overlap).first() is not None:
				return api_error("OVERLAP_CONFLICT", "A mentor is already assigned for this date range.")

			assignment.week_start_date = new_start
			assignment.week_end_date = new_end
			if assignment.question_set:
				assignment.question_set.week_start_date = new_start

		session.flush()
		return api_success(assignment.to_dict(), message="Rotation updated.")


@admin_bp.route("/mentors/rotation/<int:rotation_id>", methods=["DELETE"], strict_slashes=False)
@jwt_required()
@require_roles(UserRole.ADMIN)
def delete_rotation(rotation_id: int) -> tuple[Response, int]:
	"""Cancel and delete a mentor rotation while preserving mentor draft questions."""
	with get_db_session() as session:
		assignment = session.get(MentorAssignment, rotation_id)
		if not assignment:
			return api_error("NOT_FOUND", "Rotation not found.", status_code=404)

		# If question set is associated, unlink it from this rotation so questions are preserved in the pool
		if assignment.question_set:
			assignment.question_set.mentor_assignment_id = None
			if assignment.question_set.status == QuestionSetStatus.DRAFT:
				assignment.question_set.week_start_date = None

		session.delete(assignment)
		return api_success({"id": rotation_id}, message="Rotation deleted.")

@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@require_roles(UserRole.ADMIN)
def list_users() -> tuple[Response, int]:
	"""List users with role filtering."""
	role_filter: str | None = request.args.get("role")
	with get_db_session() as session:
		stmt = select(User)
		if role_filter and role_filter in UserRole.__members__.values():
			stmt = stmt.where(User.role == UserRole(role_filter))
		users = session.scalars(stmt.order_by(User.id.desc()).limit(100)).all()
		return api_success([u.to_dict() for u in users])


@admin_bp.route("/users", methods=["POST"])
@jwt_required()
@require_roles(UserRole.ADMIN)
def create_staff_user() -> tuple[Response, int]:
	"""Admin creates a Mentor or Admin user."""
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data:
		return api_error("INVALID_PAYLOAD", "Request body must be valid JSON.")

	name = sanitize_text(str(data.get("name", "")), max_length=128)
	email = sanitize_text(str(data.get("email", "")), max_length=255).lower()
	role_str = str(data.get("role", "mentor")).lower()
	password = str(data.get("password", "DefaultPassword@123"))

	if not name or not email or "@" not in email:
		return api_error("MISSING_FIELDS", "Valid 'name' and 'email' are required.")

	if role_str not in ("student", "mentor", "admin"):
		return api_error("INVALID_ROLE", "Role must be 'student', 'mentor', or 'admin'.")

	with get_db_session() as session:
		existing = session.scalars(select(User).where(User.email == email)).first()
		if existing:
			return api_error("DUPLICATE_EMAIL", "A user with this email already exists.")

		user = User(
			name=name,
			email=email,
			role=UserRole(role_str),
		)
		user.set_password(password)
		session.add(user)
		session.flush()

		return api_success(user.to_dict(), message="User created successfully.")


@admin_bp.route("/users/<int:user_id>", methods=["PUT"], strict_slashes=False)
@admin_bp.route("/users/<int:user_id>/", methods=["PUT"], strict_slashes=False)
@jwt_required()
@require_roles(UserRole.ADMIN)
def update_user(user_id: int) -> tuple[Response, int]:
	"""Admin updates user name, email, role, or password."""
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data:
		return api_error("INVALID_PAYLOAD", "Request body must be valid JSON.")

	with get_db_session() as session:
		user = session.get(User, user_id)
		if not user:
			return api_error("USER_NOT_FOUND", "User not found.", status_code=404)

		if "name" in data and str(data["name"]).strip():
			user.name = sanitize_text(str(data["name"]), max_length=128)

		if "email" in data and str(data["email"]).strip():
			new_email = sanitize_text(str(data["email"]), max_length=255).lower()
			if "@" not in new_email:
				return api_error("INVALID_EMAIL", "Invalid email format.")
			if new_email != user.email:
				existing = session.scalars(select(User).where(User.email == new_email)).first()
				if existing:
					return api_error("DUPLICATE_EMAIL", "A user with this email already exists.")
				user.email = new_email

		if "role" in data and str(data["role"]).strip():
			role_val = str(data["role"]).lower()
			if role_val in UserRole.__members__.values():
				user.role = UserRole(role_val)

		if "password" in data and str(data["password"]).strip():
			user.set_password(str(data["password"]).strip())

		session.flush()
		return api_success(user.to_dict(), message="User updated successfully.")


@admin_bp.route("/leaves", methods=["GET"])
@jwt_required()
@require_roles(UserRole.ADMIN)
def list_custom_leaves() -> tuple[Response, int]:
	"""List all department leaves / holidays."""
	with get_db_session() as session:
		leaves = session.scalars(select(CustomLeave).order_by(CustomLeave.start_date.asc())).all()
		return api_success([leave.to_dict() for leave in leaves])


@admin_bp.route("/leaves", methods=["POST"])
@jwt_required()
@require_roles(UserRole.ADMIN)
def create_custom_leave() -> tuple[Response, int]:
	"""Admin adds a custom department leave."""
	admin_id: int = int(get_jwt_identity())
	data: dict[str, Any] | None = request.get_json(silent=True)
	if not data:
		return api_error("INVALID_PAYLOAD", "Request body must be valid JSON.")

	title = sanitize_text(str(data.get("title", "")), max_length=128)
	start_str = str(data.get("start_date", "")).strip()
	end_str = str(data.get("end_date", "")).strip()
	description = (
		sanitize_text(str(data.get("description", "")), max_length=255)
		if data.get("description")
		else None
	)

	if not title or not start_str or not end_str:
		return api_error("MISSING_FIELDS", "'title', 'start_date', and 'end_date' are required.")

	try:
		start_date = date.fromisoformat(start_str)
		end_date = date.fromisoformat(end_str)
	except ValueError:
		return api_error("INVALID_DATE_FORMAT", "Dates must be ISO format (YYYY-MM-DD).")

	if start_date > end_date:
		return api_error("INVALID_RANGE", "'start_date' must be on or before 'end_date'.")

	with get_db_session() as session:
		leave = CustomLeave(
			title=title,
			start_date=start_date,
			end_date=end_date,
			description=description,
			created_by_admin_id=admin_id,
		)
		session.add(leave)
		session.flush()
		return api_success(leave.to_dict(), message="Custom leave scheduled.")


@admin_bp.route("/leaves/<int:leave_id>", methods=["DELETE"])
@jwt_required()
@require_roles(UserRole.ADMIN)
def delete_custom_leave(leave_id: int) -> tuple[Response, int]:
	"""Admin removes a custom leave."""
	with get_db_session() as session:
		leave = session.get(CustomLeave, leave_id)
		if not leave:
			return api_error("LEAVE_NOT_FOUND", "Leave not found.", status_code=404)
		session.delete(leave)
		return api_success({"id": leave_id}, message="Custom leave removed.")


