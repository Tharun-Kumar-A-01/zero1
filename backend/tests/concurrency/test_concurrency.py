from __future__ import annotations

import concurrent.futures
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import Config
from app.database import get_db_session
from app.models.assignment import DailyAssignment
from app.models.enums import DailyCodingStatus, DailyMCQStatus, PointsReason
from app.models.gamification import PointsLedger, Streak
from app.models.user import User
from app.services.streak_service import evaluate_daily_streak_and_points, get_student_total_points


def test_concurrent_streak_and_points_evaluation(db: Session, test_student_user: User) -> None:
	"""
	Simulate concurrent threads calling evaluate_daily_streak_and_points simultaneously.
	Verifies that row-level locking and ledger constraints prevent duplicate points/streaks.
	"""
	today = datetime.now(Config.SYSTEM_TIMEZONE).date()

	# Create assignment with MCQ and Coding solved
	assignment = DailyAssignment(
		student_id=test_student_user.id,
		assignment_date=today,
		mcq_status=DailyMCQStatus.CORRECT,
		coding_status=DailyCodingStatus.SOLVED,
	)
	db.add(assignment)
	db.commit()

	def worker_task() -> tuple[int, int, bool]:
		with get_db_session() as session:
			return evaluate_daily_streak_and_points(
				session=session, student_id=test_student_user.id, assignment_date=today
			)

	# Execute 5 concurrent threads
	results: list[tuple[int, int, bool]] = []
	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		futures = [executor.submit(worker_task) for _ in range(5)]
		for f in concurrent.futures.as_completed(futures):
			results.append(f.result())

	# Verify database state
	with get_db_session() as session:
		streak = session.query(Streak).filter_by(student_id=test_student_user.id).first()
		assert streak is not None
		assert streak.current_streak == 1  # Incremented exactly once, not 5 times!

		# Points ledger must have exactly 1 entry for MCQ and 1 entry for Coding
		mcq_entries = (
			session.query(PointsLedger)
			.filter_by(
				student_id=test_student_user.id,
				reason=PointsReason.DAILY_MCQ,
				reference_id=assignment.id,
			)
			.all()
		)
		assert len(mcq_entries) == 1
		assert mcq_entries[0].delta == 5

		code_entries = (
			session.query(PointsLedger)
			.filter_by(
				student_id=test_student_user.id,
				reason=PointsReason.DAILY_CODING,
				reference_id=assignment.id,
			)
			.all()
		)
		assert len(code_entries) == 1
		assert code_entries[0].delta == 15

		total_points: int = get_student_total_points(session, test_student_user.id)
		assert total_points == 20  # 5 + 15
