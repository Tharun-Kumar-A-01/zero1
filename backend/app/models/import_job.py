from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ImportJobStatus

if TYPE_CHECKING:
	from app.models.user import User


class ImportJob(Base):
	__tablename__ = "import_jobs"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	admin_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
	original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
	storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
	status: Mapped[ImportJobStatus] = mapped_column(
		SQLEnum(ImportJobStatus), default=ImportJobStatus.UPLOADED, nullable=False, index=True
	)
	target_year_batch: Mapped[str] = mapped_column(String(32), nullable=False)
	ai_parse_result: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
	error_log: Mapped[str | None] = mapped_column(Text, nullable=True)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
	)
	committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

	# Relationships
	admin: Mapped[User] = relationship("User")

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"admin_id": self.admin_id,
			"original_filename": self.original_filename,
			"status": self.status.value,
			"target_year_batch": self.target_year_batch,
			"ai_parse_result": self.ai_parse_result,
			"error_log": self.error_log,
			"created_at": self.created_at.isoformat(),
			"committed_at": self.committed_at.isoformat() if self.committed_at else None,
		}
