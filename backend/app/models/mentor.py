from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

from sqlalchemy import Date, Enum as SQLEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import AssignmentStatus

if TYPE_CHECKING:
	from app.models.question import QuestionSet
	from app.models.user import User


class MentorAssignment(Base):
	__tablename__ = "mentor_assignments"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
	week_start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
	week_end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
	status: Mapped[AssignmentStatus] = mapped_column(
		SQLEnum(AssignmentStatus), default=AssignmentStatus.UPCOMING, nullable=False, index=True
	)
	created_by_admin_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

	# Relationships
	mentor: Mapped[User] = relationship("User", foreign_keys=[user_id])
	admin: Mapped[User] = relationship("User", foreign_keys=[created_by_admin_id])
	question_set: Mapped[QuestionSet] = relationship(
		"QuestionSet", back_populates="assignment", uselist=False
	)

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"user_id": self.user_id,
			"mentor_name": self.mentor.name if self.mentor else None,
			"mentor_email": self.mentor.email if self.mentor else None,
			"week_start_date": self.week_start_date.isoformat(),
			"week_end_date": self.week_end_date.isoformat(),
			"status": self.status.value,
			"created_by_admin_id": self.created_by_admin_id,
		}


class CustomLeave(Base):
	__tablename__ = "custom_leaves"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	title: Mapped[str] = mapped_column(String(128), nullable=False)
	start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
	end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
	description: Mapped[str | None] = mapped_column(String(255), nullable=True)
	created_by_admin_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

	admin: Mapped[User] = relationship("User", foreign_keys=[created_by_admin_id])

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"title": self.title,
			"start_date": self.start_date.isoformat(),
			"end_date": self.end_date.isoformat(),
			"description": self.description,
			"created_by_admin_id": self.created_by_admin_id,
		}

