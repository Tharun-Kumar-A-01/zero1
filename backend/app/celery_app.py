from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from celery import Celery  # type: ignore[import-untyped]
from celery.schedules import crontab  # type: ignore[import-untyped]

from app.config import Config
from app.database import get_db_session
from app.models.assignment import CodeSubmission
from app.models.enums import AIReviewStatus
from app.services.ai_client import HardcodeReviewResult, ai_service
from app.services.lock_service import distributed_lock
from app.services.rotation_service import generate_daily_assignments_for_date, rotate_weekly_mentor

logger: logging.Logger = logging.getLogger(__name__)

# Initialize Celery using Valkey broker & backend
celery_app: Celery = Celery(
	"zero1_tasks",
	broker=Config.CELERY_BROKER_URL,
	backend=Config.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
	task_serializer="json",
	result_serializer="json",
	accept_content=["json"],
	timezone=Config.SYSTEM_TIMEZONE_STR,
	enable_utc=True,
	task_track_started=True,
)

# Celery Beat Scheduled Tasks
celery_app.conf.beat_schedule = {
	# Daily assignment generation at 23:55 local time
	"daily-assignment-generation": {
		"task": "app.celery_app.task_generate_daily_assignments",
		"schedule": crontab(hour=23, minute=55),
	},
	# Weekly mentor rotation check every Monday at 00:01
	"weekly-mentor-rotation": {
		"task": "app.celery_app.task_rotate_weekly_mentor",
		"schedule": crontab(hour=0, minute=1, day_of_week="monday"),
	},
}


@celery_app.task(name="app.celery_app.task_ai_hardcode_review", bind=True, max_retries=2)
def task_ai_hardcode_review(self: Any, submission_id: int) -> dict[str, str]:
	"""Asynchronously evaluate passing code submissions for hardcoded shortcuts."""
	with get_db_session() as session:
		submission: CodeSubmission | None = session.get(CodeSubmission, submission_id)
		if not submission:
			return {"status": "skipped", "reason": "submission_not_found"}

		assignment = submission.assignment
		if not assignment or not assignment.coding_question:
			return {"status": "skipped", "reason": "question_not_found"}

		coding_q = assignment.coding_question
		sample_cases: list[dict[str, str]] = [
			{"input": tc.input_data, "expected_output": tc.expected_output}
			for tc in coding_q.test_cases
			if tc.is_sample
		]

		try:
			review: HardcodeReviewResult = ai_service.review_code_for_hardcoding(
				problem_title=coding_q.title,
				problem_text=coding_q.word_problem_text,
				student_code=submission.source_code,
				sample_cases=sample_cases,
			)
			submission.ai_review_status = (
				AIReviewStatus.FLAGGED if review.status == "flagged" else AIReviewStatus.CLEAN
			)
			submission.ai_review_notes = review.reason
			return {"status": "completed", "verdict": review.status}
		except Exception as exc:
			logger.error("AI review task failed for submission %d: %s", submission_id, str(exc))
			submission.ai_review_status = AIReviewStatus.ERROR
			submission.ai_review_notes = f"AI review failed: {exc}"
			return {"status": "error", "error": str(exc)}


@celery_app.task(name="app.celery_app.task_generate_daily_assignments")
def task_generate_daily_assignments() -> str:
	"""Daily midnight scheduled task to generate tomorrow's practice assignments."""
	with distributed_lock("daily_assignment_rollover", timeout_seconds=300) as acquired:
		if not acquired:
			return "Skipped: lock held by another worker"

		tomorrow = datetime.now(Config.SYSTEM_TIMEZONE).date()
		with get_db_session() as session:
			count = generate_daily_assignments_for_date(session, tomorrow)
			return f"Generated {count} assignments for {tomorrow.isoformat()}"


@celery_app.task(name="app.celery_app.task_rotate_weekly_mentor")
def task_rotate_weekly_mentor() -> str:
	"""Weekly Monday rotation check to update active mentor."""
	with distributed_lock("weekly_mentor_rotation", timeout_seconds=300) as acquired:
		if not acquired:
			return "Skipped: lock held by another worker"

		today = datetime.now(Config.SYSTEM_TIMEZONE).date()
		with get_db_session() as session:
			rotate_weekly_mentor(session, today)
			return f"Rotation checked for {today.isoformat()}"
