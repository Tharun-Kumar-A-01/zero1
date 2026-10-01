from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.database import Base
from app.models.enums import UserRole

if TYPE_CHECKING:
	from app.models.assignment import DailyAssignment
	from app.models.gamification import PointsLedger, Streak


class User(Base):
	__tablename__ = "users"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	name: Mapped[str] = mapped_column(String(128), nullable=False)
	email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
	password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
	role: Mapped[UserRole] = mapped_column(
		SQLEnum(UserRole), default=UserRole.STUDENT, nullable=False, index=True
	)

	# Student-specific fields
	roll_number: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
	year_batch: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
	department: Mapped[str | None] = mapped_column(String(64), nullable=True)
	section: Mapped[str | None] = mapped_column(String(16), nullable=True)

	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
	)

	# Relationships
	streak: Mapped[Streak] = relationship("Streak", back_populates="student", uselist=False)
	points_records: Mapped[list[PointsLedger]] = relationship(
		"PointsLedger", back_populates="student"
	)
	daily_assignments: Mapped[list[DailyAssignment]] = relationship(
		"DailyAssignment", back_populates="student"
	)

	def set_password(self, password: str) -> None:
		self.password_hash = generate_password_hash(password)

	def check_password(self, password: str) -> bool:
		return check_password_hash(self.password_hash, password)

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"name": self.name,
			"email": self.email,
			"role": self.role.value,
			"roll_number": self.roll_number,
			"year_batch": self.year_batch,
			"department": self.department,
			"section": self.section,
			"is_active": self.is_active,
			"created_at": self.created_at.isoformat() if self.created_at else None,
		}
