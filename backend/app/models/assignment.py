from __future__ import annotations

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
	Date,
	DateTime,
	Enum as SQLEnum,
	ForeignKey,
	Integer,
	String,
	Text,
	UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import AIReviewStatus, DailyCodingStatus, DailyMCQStatus, ExecutionStatus

if TYPE_CHECKING:
	from app.models.question import CodingQuestion, MCQQuestion
	from app.models.user import User


class DailyAssignment(Base):
	__tablename__ = "daily_assignments"
	__table_args__ = (
		UniqueConstraint("student_id", "assignment_date", name="uq_student_assignment_date"),
	)

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
	assignment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

	mcq_question_id: Mapped[int | None] = mapped_column(
		ForeignKey("mcq_questions.id", ondelete="SET NULL"), nullable=True
	)
	coding_question_id: Mapped[int | None] = mapped_column(
		ForeignKey("coding_questions.id", ondelete="SET NULL"), nullable=True
	)

	mcq_status: Mapped[DailyMCQStatus] = mapped_column(
		SQLEnum(DailyMCQStatus), default=DailyMCQStatus.PENDING, nullable=False, index=True
	)
	coding_status: Mapped[DailyCodingStatus] = mapped_column(
		SQLEnum(DailyCodingStatus), default=DailyCodingStatus.PENDING, nullable=False, index=True
	)
	coding_started_at: Mapped[datetime | None] = mapped_column(
		DateTime(timezone=True), nullable=True
	)
	coding_completed_at: Mapped[datetime | None] = mapped_column(
		DateTime(timezone=True), nullable=True
	)
	coding_time_spent_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
	submission_attempts_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
	)

	# Relationships
	student: Mapped[User] = relationship("User", back_populates="daily_assignments")
	mcq_question: Mapped[MCQQuestion | None] = relationship("MCQQuestion")
	coding_question: Mapped[CodingQuestion | None] = relationship("CodingQuestion")
	mcq_submissions: Mapped[list[MCQSubmission]] = relationship(
		"MCQSubmission", back_populates="assignment"
	)
	code_submissions: Mapped[list[CodeSubmission]] = relationship(
		"CodeSubmission", back_populates="assignment"
	)

	def to_dict(self) -> dict[str, Any]:
		now = datetime.now(UTC)
		elapsed_seconds: int | None = None
		if self.coding_started_at:
			started_at = (
				self.coding_started_at
				if self.coding_started_at.tzinfo
				else self.coding_started_at.replace(tzinfo=UTC)
			)
			elapsed_seconds = max(0, int((now - started_at).total_seconds()))

		return {
			"id": self.id,
			"student_id": self.student_id,
			"assignment_date": self.assignment_date.isoformat(),
			"mcq_question": self.mcq_question.to_dict(include_answer=False)
			if self.mcq_question
			else None,
			"coding_question": self.coding_question.to_dict() if self.coding_question else None,
			"mcq_status": self.mcq_status.value,
			"coding_status": self.coding_status.value,
			"coding_started_at": self.coding_started_at.isoformat() if self.coding_started_at else None,
			"coding_completed_at": self.coding_completed_at.isoformat() if self.coding_completed_at else None,
			"coding_time_spent_seconds": self.coding_time_spent_seconds,
			"elapsed_seconds": elapsed_seconds,
			"submission_attempts_count": self.submission_attempts_count,
			"created_at": self.created_at.isoformat(),
		}


class MCQSubmission(Base):
	__tablename__ = "mcq_submissions"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	daily_assignment_id: Mapped[int] = mapped_column(
		ForeignKey("daily_assignments.id"), nullable=False, index=True
	)
	selected_option_index: Mapped[int] = mapped_column(Integer, nullable=False)
	is_correct: Mapped[bool] = mapped_column(nullable=False)
	submitted_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
	)

	# Relationships
	assignment: Mapped[DailyAssignment] = relationship(
		"DailyAssignment", back_populates="mcq_submissions"
	)

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"daily_assignment_id": self.daily_assignment_id,
			"selected_option_index": self.selected_option_index,
			"is_correct": self.is_correct,
			"submitted_at": self.submitted_at.isoformat(),
		}


class CodeSubmission(Base):
	__tablename__ = "code_submissions"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	daily_assignment_id: Mapped[int] = mapped_column(
		ForeignKey("daily_assignments.id"), nullable=False, index=True
	)
	language: Mapped[str] = mapped_column(String(32), nullable=False)
	source_code: Mapped[str] = mapped_column(Text, nullable=False)
	judge0_token: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
	execution_status: Mapped[ExecutionStatus] = mapped_column(
		SQLEnum(ExecutionStatus), default=ExecutionStatus.QUEUED, nullable=False, index=True
	)
	test_cases_passed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
	test_cases_total_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
	runtime_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
	memory_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)
	compiler_output: Mapped[str | None] = mapped_column(Text, nullable=True)

	# Anti-cheat AI review
	ai_review_status: Mapped[AIReviewStatus] = mapped_column(
		SQLEnum(AIReviewStatus), default=AIReviewStatus.PENDING, nullable=False, index=True
	)
	ai_review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

	submitted_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
	)

	# Relationships
	assignment: Mapped[DailyAssignment] = relationship(
		"DailyAssignment", back_populates="code_submissions"
	)

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"daily_assignment_id": self.daily_assignment_id,
			"language": self.language,
			"execution_status": self.execution_status.value,
			"test_cases_passed_count": self.test_cases_passed_count,
			"test_cases_total_count": self.test_cases_total_count,
			"runtime_ms": self.runtime_ms,
			"memory_kb": self.memory_kb,
			"compiler_output": self.compiler_output,
			"ai_review_status": self.ai_review_status.value,
			"ai_review_notes": self.ai_review_notes,
			"submitted_at": self.submitted_at.isoformat(),
		}
