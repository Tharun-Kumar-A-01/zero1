from __future__ import annotations

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
	Boolean,
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
from app.models.enums import MilestoneThresholdType, PointsReason, RewardType

if TYPE_CHECKING:
	from app.models.user import User


class Streak(Base):
	__tablename__ = "streaks"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	student_id: Mapped[int] = mapped_column(
		ForeignKey("users.id"), unique=True, nullable=False, index=True
	)
	current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
	longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
	last_active_date: Mapped[date | None] = mapped_column(Date, nullable=True)
	freeze_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

	# Relationships
	student: Mapped[User] = relationship("User", back_populates="streak")

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"student_id": self.student_id,
			"current_streak": self.current_streak,
			"longest_streak": self.longest_streak,
			"last_active_date": self.last_active_date.isoformat()
			if self.last_active_date
			else None,
			"freeze_tokens": self.freeze_tokens,
		}


class Milestone(Base):
	__tablename__ = "milestones"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	name: Mapped[str] = mapped_column(String(128), nullable=False)
	description: Mapped[str] = mapped_column(Text, nullable=False)
	threshold_type: Mapped[MilestoneThresholdType] = mapped_column(
		SQLEnum(MilestoneThresholdType), nullable=False
	)
	threshold_value: Mapped[int] = mapped_column(Integer, nullable=False)
	reward_id: Mapped[int] = mapped_column(ForeignKey("rewards.id"), nullable=False)
	created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

	# Relationships
	reward: Mapped[Reward] = relationship("Reward", back_populates="milestones")

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"name": self.name,
			"description": self.description,
			"threshold_type": self.threshold_type.value,
			"threshold_value": self.threshold_value,
			"reward_id": self.reward_id,
			"reward": self.reward.to_dict() if self.reward else None,
			"is_active": self.is_active,
		}


class Reward(Base):
	__tablename__ = "rewards"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	type: Mapped[RewardType] = mapped_column(SQLEnum(RewardType), nullable=False)
	name: Mapped[str] = mapped_column(String(128), nullable=False)
	description: Mapped[str] = mapped_column(Text, nullable=False)
	icon_asset_ref: Mapped[str] = mapped_column(String(128), default="pi-star", nullable=False)
	points_value: Mapped[int | None] = mapped_column(Integer, nullable=True)

	# Relationships
	milestones: Mapped[list[Milestone]] = relationship("Milestone", back_populates="reward")
	student_rewards: Mapped[list[StudentReward]] = relationship(
		"StudentReward", back_populates="reward"
	)

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"type": self.type.value,
			"name": self.name,
			"description": self.description,
			"icon_asset_ref": self.icon_asset_ref,
			"points_value": self.points_value,
		}


class StudentReward(Base):
	__tablename__ = "student_rewards"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
	reward_id: Mapped[int] = mapped_column(ForeignKey("rewards.id"), nullable=False, index=True)
	milestone_id: Mapped[int | None] = mapped_column(ForeignKey("milestones.id"), nullable=True)
	awarded_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
	)

	# Relationships
	reward: Mapped[Reward] = relationship("Reward", back_populates="student_rewards")

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"student_id": self.student_id,
			"reward_id": self.reward_id,
			"reward": self.reward.to_dict() if self.reward else None,
			"milestone_id": self.milestone_id,
			"awarded_at": self.awarded_at.isoformat(),
		}


class PointsLedger(Base):
	__tablename__ = "points_ledger"
	__table_args__ = (
		UniqueConstraint("student_id", "reason", "reference_id", name="uq_points_ledger_reference"),
	)

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
	delta: Mapped[int] = mapped_column(Integer, nullable=False)
	reason: Mapped[PointsReason] = mapped_column(SQLEnum(PointsReason), nullable=False)
	reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
	)

	# Relationships
	student: Mapped[User] = relationship("User", back_populates="points_records")

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"student_id": self.student_id,
			"delta": self.delta,
			"reason": self.reason.value,
			"reference_id": self.reference_id,
			"created_at": self.created_at.isoformat(),
		}
