from __future__ import annotations

import logging
import random
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assignment import DailyAssignment
from app.models.enums import AssignmentStatus, QuestionSetStatus, UserRole
from app.models.mentor import MentorAssignment
from app.models.question import CodingQuestion, MCQQuestion, QuestionSet
from app.models.user import User

logger: logging.Logger = logging.getLogger(__name__)


def get_active_or_fallback_question_set(session: Session, target_date: date) -> QuestionSet | None:
	"""
	Locate the active published question set for the week.
	If missing or unpublished, fall back to the most recent published/archived set.
	"""
	# 1. Check for published set matching active mentor assignment
	stmt_active = (
		select(QuestionSet)
		.join(MentorAssignment)
		.where(
			MentorAssignment.week_start_date <= target_date,
			MentorAssignment.week_end_date >= target_date,
			QuestionSet.status == QuestionSetStatus.PUBLISHED,
		)
	)
	active_set: QuestionSet | None = session.scalars(stmt_active).first()
	if active_set:
		return active_set

	# 2. Fallback: select any published or archived question set
	stmt_fallback = (
		select(QuestionSet)
		.where(QuestionSet.status.in_([QuestionSetStatus.PUBLISHED, QuestionSetStatus.ARCHIVED]))
		.order_by(QuestionSet.id.desc())
	)
	fallback_set: QuestionSet | None = session.scalars(stmt_fallback).first()
	return fallback_set


def generate_daily_assignments_for_date(session: Session, target_date: date) -> int:
	"""
	Generate daily assignments for all active students for target_date.
	Ensures tamper-proof, randomized selection from the pool without repetition.
	"""
	question_set: QuestionSet | None = get_active_or_fallback_question_set(session, target_date)
	if not question_set:
		logger.warning(
			"No question set found for %s. Cannot generate assignments.", target_date.isoformat()
		)
		return 0

	# Retrieve question pools
	mcq_pool: list[MCQQuestion] = list(question_set.mcq_questions)
	coding_pool: list[CodingQuestion] = list(question_set.coding_questions)

	if not mcq_pool and not coding_pool:
		logger.warning("Question set %d has no questions.", question_set.id)
		return 0

	# Get all active students
	stmt_students = select(User).where(User.role == UserRole.STUDENT, User.is_active.is_(True))
	active_students: list[User] = list(session.scalars(stmt_students).all())

	created_count: int = 0

	for student in active_students:
		# Check if assignment already exists
		stmt_exists = select(DailyAssignment).where(
			DailyAssignment.student_id == student.id, DailyAssignment.assignment_date == target_date
		)
		if session.scalars(stmt_exists).first() is not None:
			continue

		# Anti-repeat selection for MCQs
		served_mcq_ids_stmt = select(DailyAssignment.mcq_question_id).where(
			DailyAssignment.student_id == student.id, DailyAssignment.mcq_question_id.is_not(None)
		)
		served_mcq_ids: set[int] = {
			qid for qid in session.scalars(served_mcq_ids_stmt).all() if qid is not None
		}
		available_mcqs: list[MCQQuestion] = [q for q in mcq_pool if q.id not in served_mcq_ids]
		chosen_mcq: MCQQuestion | None = (
			random.choice(available_mcqs)
			if available_mcqs
			else (random.choice(mcq_pool) if mcq_pool else None)
		)

		# Anti-repeat selection for Coding
		served_coding_ids_stmt = select(DailyAssignment.coding_question_id).where(
			DailyAssignment.student_id == student.id,
			DailyAssignment.coding_question_id.is_not(None),
		)
		served_coding_ids: set[int] = {
			cid for cid in session.scalars(served_coding_ids_stmt).all() if cid is not None
		}
		available_coding: list[CodingQuestion] = [
			q for q in coding_pool if q.id not in served_coding_ids
		]
		chosen_coding: CodingQuestion | None = (
			random.choice(available_coding)
			if available_coding
			else (random.choice(coding_pool) if coding_pool else None)
		)

		new_assignment = DailyAssignment(
			student_id=student.id,
			assignment_date=target_date,
			mcq_question_id=chosen_mcq.id if chosen_mcq else None,
			coding_question_id=chosen_coding.id if chosen_coding else None,
		)
		session.add(new_assignment)
		created_count += 1

	session.flush()
	return created_count


def rotate_weekly_mentor(session: Session, current_date: date) -> None:
	"""Advance mentor assignments based on date."""
	# Complete past assignments
	stmt_past = (
		select(MentorAssignment)
		.where(
			MentorAssignment.week_end_date < current_date,
			MentorAssignment.status == AssignmentStatus.ACTIVE,
		)
		.with_for_update()
	)
	past_assignments: list[MentorAssignment] = list(session.scalars(stmt_past).all())
	for assignment in past_assignments:
		if (
			assignment.question_set
			and assignment.question_set.status == QuestionSetStatus.PUBLISHED
		):
			assignment.status = AssignmentStatus.COMPLETED
		else:
			assignment.status = AssignmentStatus.MISSED

	# Activate current assignment
	stmt_current = (
		select(MentorAssignment)
		.where(
			MentorAssignment.week_start_date <= current_date,
			MentorAssignment.week_end_date >= current_date,
			MentorAssignment.status == AssignmentStatus.UPCOMING,
		)
		.with_for_update()
	)
	current_assignment: MentorAssignment | None = session.scalars(stmt_current).first()
	if current_assignment:
		current_assignment.status = AssignmentStatus.ACTIVE

	session.flush()
