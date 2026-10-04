from __future__ import annotations

import threading
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Config
from app.models.assignment import DailyAssignment
from app.models.enums import DailyCodingStatus, DailyMCQStatus, PointsReason
from app.models.gamification import PointsLedger, Streak

_sqlite_mutex: threading.Lock = threading.Lock()


def get_student_total_points(session: Session, student_id: int) -> int:
	"""
	Always compute total points as SUM(points_ledger.delta).
	Never store a mutable running total on the user row.
	"""
	stmt = select(func.coalesce(func.sum(PointsLedger.delta), 0)).where(
		PointsLedger.student_id == student_id
	)
	total: int = session.scalar(stmt) or 0
	return total


def evaluate_daily_streak_and_points(
	session: Session, student_id: int, assignment_date: date
) -> tuple[int, int, bool]:
	"""
	Deterministically calculate streaks and points using pessimistic locking.
	Returns: (current_streak: int, points_awarded: int, is_solved_today: bool)
	"""
	is_sqlite: bool = getattr(session.get_bind().dialect, "name", "") == "sqlite"
	if is_sqlite:
		_sqlite_mutex.acquire()
	try:
		return _evaluate_daily_streak_and_points_impl(session, student_id, assignment_date)
	finally:
		if is_sqlite:
			_sqlite_mutex.release()


def _evaluate_daily_streak_and_points_impl(
	session: Session, student_id: int, assignment_date: date
) -> tuple[int, int, bool]:
	# 1. Acquire exclusive row-level lock on the student's streak record
	stmt_streak = select(Streak).where(Streak.student_id == student_id).with_for_update()
	streak_record: Streak | None = session.scalars(stmt_streak).first()

	if streak_record is None:
		try:
			with session.begin_nested():
				streak_record = Streak(
					student_id=student_id,
					current_streak=0,
					longest_streak=0,
					last_active_date=None,
					freeze_tokens=0,
				)
				session.add(streak_record)
				session.flush()
		except Exception:
			streak_record = session.scalars(stmt_streak).first()

	# If still none for any reason, re-query
	if streak_record is None:
		streak_record = session.scalars(stmt_streak).first()
		if streak_record is None:
			return 0, 0, False

	# 2. Fetch the student's daily assignment for the date
	stmt_assignment = (
		select(DailyAssignment)
		.where(
			DailyAssignment.student_id == student_id,
			DailyAssignment.assignment_date == assignment_date,
		)
		.with_for_update()
	)
	assignment: DailyAssignment | None = session.scalars(stmt_assignment).first()
	if assignment is None:
		return streak_record.current_streak, 0, False

	mcq_solved: bool = assignment.mcq_status == DailyMCQStatus.CORRECT
	coding_solved: bool = assignment.coding_status == DailyCodingStatus.SOLVED

	if Config.STREAK_REQUIRES_BOTH:
		day_solved: bool = mcq_solved and coding_solved
	else:
		day_solved = mcq_solved or coding_solved

	points_awarded: int = 0

	# 3. Award points for MCQ if newly solved and not previously awarded
	if mcq_solved:
		stmt_mcq_points = select(PointsLedger).where(
			PointsLedger.student_id == student_id,
			PointsLedger.reason == PointsReason.DAILY_MCQ,
			PointsLedger.reference_id == assignment.id,
		)
		if session.scalars(stmt_mcq_points).first() is None:
			try:
				with session.begin_nested():
					ledger_mcq = PointsLedger(
						student_id=student_id,
						delta=5,
						reason=PointsReason.DAILY_MCQ,
						reference_id=assignment.id,
					)
					session.add(ledger_mcq)
					session.flush()
					points_awarded += 5
			except Exception:
				pass

	# 4. Award points for Coding if newly solved and not previously awarded
	if coding_solved:
		stmt_code_points = select(PointsLedger).where(
			PointsLedger.student_id == student_id,
			PointsLedger.reason == PointsReason.DAILY_CODING,
			PointsLedger.reference_id == assignment.id,
		)
		if session.scalars(stmt_code_points).first() is None:
			try:
				with session.begin_nested():
					ledger_coding = PointsLedger(
						student_id=student_id,
						delta=15,
						reason=PointsReason.DAILY_CODING,
						reference_id=assignment.id,
					)
					session.add(ledger_coding)
					session.flush()
					points_awarded += 15
			except Exception:
				pass

	# 5. Calculate streak progression if day criteria is satisfied
	if day_solved:
		if streak_record.last_active_date == assignment_date:
			# Already credited for today; do not increment streak again
			pass
		elif streak_record.last_active_date == (assignment_date - timedelta(days=1)):
			# Consecutive active day
			streak_record.current_streak += 1
			streak_record.last_active_date = assignment_date
		else:
			# Gap between days; reset streak to 1
			streak_record.current_streak = 1
			streak_record.last_active_date = assignment_date

		if streak_record.current_streak > streak_record.longest_streak:
			streak_record.longest_streak = streak_record.current_streak

	session.flush()
	return streak_record.current_streak, points_awarded, day_solved
