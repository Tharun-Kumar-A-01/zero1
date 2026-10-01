from __future__ import annotations

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
	JSON,
	Boolean,
	Date,
	DateTime,
	Enum as SQLEnum,
	Float,
	ForeignKey,
	Integer,
	String,
	Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import DifficultyLevel, QuestionSetStatus, TestCaseSource

if TYPE_CHECKING:
	from app.models.mentor import MentorAssignment


class QuestionSet(Base):
	__tablename__ = "question_sets"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	mentor_assignment_id: Mapped[int] = mapped_column(
		ForeignKey("mentor_assignments.id"), nullable=False, index=True
	)
	week_start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
	status: Mapped[QuestionSetStatus] = mapped_column(
		SQLEnum(QuestionSetStatus), default=QuestionSetStatus.DRAFT, nullable=False, index=True
	)

	# Relationships
	assignment: Mapped[MentorAssignment] = relationship(
		"MentorAssignment", back_populates="question_set"
	)
	mcq_questions: Mapped[list[MCQQuestion]] = relationship(
		"MCQQuestion", back_populates="question_set", cascade="all, delete-orphan"
	)
	coding_questions: Mapped[list[CodingQuestion]] = relationship(
		"CodingQuestion", back_populates="question_set", cascade="all, delete-orphan"
	)

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"mentor_assignment_id": self.mentor_assignment_id,
			"week_start_date": self.week_start_date.isoformat(),
			"status": self.status.value,
			"mcq_count": len(self.mcq_questions) if self.mcq_questions else 0,
			"coding_count": len(self.coding_questions) if self.coding_questions else 0,
		}


class MCQQuestion(Base):
	__tablename__ = "mcq_questions"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	question_set_id: Mapped[int] = mapped_column(
		ForeignKey("question_sets.id"), nullable=False, index=True
	)
	prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
	options: Mapped[list[str]] = mapped_column(JSON, nullable=False)
	correct_option_index: Mapped[int] = mapped_column(Integer, nullable=False)
	explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
	difficulty: Mapped[DifficultyLevel] = mapped_column(
		SQLEnum(DifficultyLevel), default=DifficultyLevel.MEDIUM, nullable=False
	)
	tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
	)

	# Relationships
	question_set: Mapped[QuestionSet] = relationship("QuestionSet", back_populates="mcq_questions")

	def to_dict(self, include_answer: bool = False) -> dict[str, Any]:
		data: dict[str, Any] = {
			"id": self.id,
			"question_set_id": self.question_set_id,
			"prompt_text": self.prompt_text,
			"options": self.options,
			"difficulty": self.difficulty.value,
			"tags": self.tags,
			"created_at": self.created_at.isoformat(),
		}
		if include_answer:
			data["correct_option_index"] = self.correct_option_index
			data["explanation"] = self.explanation
		return data


class CodingQuestion(Base):
	__tablename__ = "coding_questions"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	question_set_id: Mapped[int] = mapped_column(
		ForeignKey("question_sets.id"), nullable=False, index=True
	)
	title: Mapped[str] = mapped_column(String(255), nullable=False)
	word_problem_text: Mapped[str] = mapped_column(Text, nullable=False)
	constraints_text: Mapped[str] = mapped_column(Text, nullable=False)
	difficulty: Mapped[DifficultyLevel] = mapped_column(
		SQLEnum(DifficultyLevel), default=DifficultyLevel.MEDIUM, nullable=False
	)
	allowed_languages: Mapped[list[str]] = mapped_column(
		JSON, default=lambda: ["python", "cpp", "java"], nullable=False
	)
	time_limit_ms: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
	memory_limit_kb: Mapped[int] = mapped_column(Integer, default=128000, nullable=False)
	forbidden_constructs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
	)

	# Relationships
	question_set: Mapped[QuestionSet] = relationship(
		"QuestionSet", back_populates="coding_questions"
	)
	test_cases: Mapped[list[CodingTestCase]] = relationship(
		"CodingTestCase", back_populates="coding_question", cascade="all, delete-orphan"
	)

	def to_dict(self, include_hidden_tests: bool = False) -> dict[str, Any]:
		sample_tests: list[dict[str, Any]] = [
			tc.to_dict() for tc in self.test_cases if tc.is_sample
		]
		data: dict[str, Any] = {
			"id": self.id,
			"question_set_id": self.question_set_id,
			"title": self.title,
			"word_problem_text": self.word_problem_text,
			"constraints_text": self.constraints_text,
			"difficulty": self.difficulty.value,
			"allowed_languages": self.allowed_languages,
			"time_limit_ms": self.time_limit_ms,
			"memory_limit_kb": self.memory_limit_kb,
			"sample_test_cases": sample_tests,
			"created_at": self.created_at.isoformat(),
		}
		if include_hidden_tests:
			data["all_test_cases"] = [tc.to_dict() for tc in self.test_cases]
		return data


class CodingTestCase(Base):
	__tablename__ = "coding_test_cases"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	coding_question_id: Mapped[int] = mapped_column(
		ForeignKey("coding_questions.id"), nullable=False, index=True
	)
	input_data: Mapped[str] = mapped_column(Text, nullable=False)
	expected_output: Mapped[str] = mapped_column(Text, nullable=False)
	is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
	is_stress_case: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
	source: Mapped[TestCaseSource] = mapped_column(
		SQLEnum(TestCaseSource), default=TestCaseSource.MENTOR_MANUAL, nullable=False
	)
	weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

	# Relationships
	coding_question: Mapped[CodingQuestion] = relationship(
		"CodingQuestion", back_populates="test_cases"
	)

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"input_data": self.input_data,
			"expected_output": self.expected_output,
			"is_sample": self.is_sample,
			"is_stress_case": self.is_stress_case,
			"source": self.source.value,
			"weight": self.weight,
		}
