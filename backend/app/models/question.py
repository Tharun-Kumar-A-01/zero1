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
	from app.models.user import User


class QuestionSet(Base):
	__tablename__ = "question_sets"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	mentor_assignment_id: Mapped[int | None] = mapped_column(
		ForeignKey("mentor_assignments.id"), nullable=True, index=True
	)
	mentor_id: Mapped[int | None] = mapped_column(
		ForeignKey("users.id"), nullable=True, index=True
	)
	week_start_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
	status: Mapped[QuestionSetStatus] = mapped_column(
		SQLEnum(QuestionSetStatus), default=QuestionSetStatus.DRAFT, nullable=False, index=True
	)

	# Relationships
	assignment: Mapped[MentorAssignment | None] = relationship(
		"MentorAssignment", back_populates="question_set"
	)
	mentor: Mapped[User | None] = relationship("User", foreign_keys=[mentor_id])
	mcq_questions: Mapped[list[MCQQuestion]] = relationship(
		"MCQQuestion", back_populates="question_set", cascade="all, delete-orphan"
	)
	coding_questions: Mapped[list[CodingQuestion]] = relationship(
		"CodingQuestion", back_populates="question_set", cascade="all, delete-orphan"
	)

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"mentor_id": self.mentor_id,
			"mentor_assignment_id": self.mentor_assignment_id,
			"week_start_date": self.week_start_date.isoformat() if self.week_start_date else None,
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
		JSON, default=lambda: ["python", "cpp", "java", "c"], nullable=False
	)
	time_limit_ms: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
	memory_limit_kb: Mapped[int] = mapped_column(Integer, default=128000, nullable=False)
	forbidden_constructs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
	function_name: Mapped[str] = mapped_column(String(100), default="solve", nullable=False)
	parameter_definitions: Mapped[list[dict[str, Any]]] = mapped_column(
		JSON, default=list, nullable=False
	)
	return_type: Mapped[str] = mapped_column(String(50), default="int", nullable=False)
	starter_templates: Mapped[dict[str, str]] = mapped_column(
		JSON, default=dict, nullable=False
	)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
	)

	# Relationships
	question_set: Mapped[QuestionSet] = relationship(
		"QuestionSet", back_populates="coding_questions"
	)
	sample_test_cases: Mapped[list[CodingSampleTestCase]] = relationship(
		"CodingSampleTestCase",
		back_populates="coding_question",
		cascade="all, delete-orphan",
		order_by="CodingSampleTestCase.id",
	)
	hidden_test_cases: Mapped[list[CodingHiddenTestCase]] = relationship(
		"CodingHiddenTestCase",
		back_populates="coding_question",
		cascade="all, delete-orphan",
		order_by="CodingHiddenTestCase.id",
	)
	legacy_test_cases: Mapped[list[CodingTestCase]] = relationship(
		"CodingTestCase", back_populates="coding_question", cascade="all, delete-orphan"
	)

	@property
	def test_cases(self) -> list[Any]:
		if self.sample_test_cases or self.hidden_test_cases:
			return list(self.sample_test_cases) + list(self.hidden_test_cases)
		return list(self.legacy_test_cases)

	def to_dict(self, include_hidden_tests: bool = False) -> dict[str, Any]:
		samples = [tc.to_dict() for tc in self.sample_test_cases]
		if not samples and self.legacy_test_cases:
			samples = [tc.to_dict() for tc in self.legacy_test_cases if tc.is_sample]

		fn: str = self.function_name or "solve"
		params: list[dict[str, Any]] = list(self.parameter_definitions) if self.parameter_definitions else []
		ret: str = self.return_type or "int"
		templates: dict[str, str] = dict(self.starter_templates) if self.starter_templates else {}

		if not templates or not params or any("def solve(self, *args):" in v for v in templates.values()):
			from app.services.code_boilerplate import (
				generate_boilerplate_templates,
				resolve_problem_signature,
			)

			fn, inferred_params, ret = resolve_problem_signature(
				title=self.title,
				function_name=self.function_name,
				parameters=self.parameter_definitions,
				return_type=self.return_type,
				sample_cases=samples,
				problem_text=self.word_problem_text,
			)
			params = list(inferred_params)
			templates = generate_boilerplate_templates(fn, params, ret)

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
			"function_name": fn,
			"parameter_definitions": params,
			"return_type": ret,
			"starter_templates": templates,
			"sample_test_cases": samples,
			"created_at": self.created_at.isoformat(),
		}
		if include_hidden_tests:
			hiddens = [tc.to_dict() for tc in self.hidden_test_cases]
			if not hiddens and self.legacy_test_cases:
				hiddens = [tc.to_dict() for tc in self.legacy_test_cases if not tc.is_sample]
			data["hidden_test_cases"] = hiddens
			data["all_test_cases"] = samples + hiddens
		return data


class CodingSampleTestCase(Base):
	__tablename__ = "coding_sample_test_cases"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	coding_question_id: Mapped[int] = mapped_column(
		ForeignKey("coding_questions.id"), nullable=False, index=True
	)
	input_data: Mapped[str] = mapped_column(Text, nullable=False)
	expected_output: Mapped[str] = mapped_column(Text, nullable=False)
	weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

	# Relationships
	coding_question: Mapped[CodingQuestion] = relationship(
		"CodingQuestion", back_populates="sample_test_cases"
	)

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"input_data": self.input_data,
			"expected_output": self.expected_output,
			"is_sample": True,
			"is_stress_case": False,
			"source": "mentor_manual",
			"weight": self.weight,
		}


class CodingHiddenTestCase(Base):
	__tablename__ = "coding_hidden_test_cases"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	coding_question_id: Mapped[int] = mapped_column(
		ForeignKey("coding_questions.id"), nullable=False, index=True
	)
	input_data: Mapped[str] = mapped_column(Text, nullable=False)
	expected_output: Mapped[str] = mapped_column(Text, nullable=False)
	weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

	# Relationships
	coding_question: Mapped[CodingQuestion] = relationship(
		"CodingQuestion", back_populates="hidden_test_cases"
	)

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"input_data": self.input_data,
			"expected_output": self.expected_output,
			"is_sample": False,
			"is_stress_case": False,
			"source": "mentor_manual",
			"weight": self.weight,
		}


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
		"CodingQuestion", back_populates="legacy_test_cases"
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
