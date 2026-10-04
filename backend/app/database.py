from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, scoped_session, sessionmaker

from app.config import Config

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
	"""Base declarative class for all SQLAlchemy 2.0 models."""

	pass


# Configure engine options conditionally for PostgreSQL vs SQLite (testing)
engine_kwargs: dict[str, Any] = {
	"pool_pre_ping": True,
}
if "sqlite" not in Config.DATABASE_URL:
	engine_kwargs["pool_size"] = 10
	engine_kwargs["max_overflow"] = 20

engine = create_engine(Config.DATABASE_URL, **engine_kwargs)

# Thread-safe scoped session factory
SessionFactory: sessionmaker[Session] = sessionmaker(
	bind=engine,
	autoflush=False,
	autocommit=False,
	expire_on_commit=False,
)
db_session: scoped_session[Session] = scoped_session(SessionFactory)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
	"""Provide a transactional database session scope with automatic rollback on error."""
	session: Session = db_session()
	try:
		yield session
		session.commit()
	except Exception:
		session.rollback()
		raise
	finally:
		session.close()


def init_db() -> None:
	"""Create all registered database tables and apply required schema migrations."""
	Base.metadata.create_all(bind=engine)
	if "sqlite" not in Config.DATABASE_URL:
		try:
			with engine.connect() as conn:
				conn.execute(
					text(
						"ALTER TABLE question_sets ALTER COLUMN mentor_assignment_id DROP NOT NULL;"
					)
				)
				conn.execute(
					text("ALTER TABLE question_sets ALTER COLUMN week_start_date DROP NOT NULL;")
				)
				conn.execute(
					text("""
					DO $$
					BEGIN
						IF NOT EXISTS (
							SELECT 1 FROM information_schema.columns
							WHERE table_name='question_sets' AND column_name='mentor_id'
						) THEN
							ALTER TABLE question_sets ADD COLUMN mentor_id INTEGER REFERENCES users(id);
						END IF;
					END $$;
				""")
				)
				# Migrations for daily_assignments columns
				conn.execute(
					text("""
					DO $$
					BEGIN
						IF NOT EXISTS (
							SELECT 1 FROM information_schema.columns
							WHERE table_name='daily_assignments' AND column_name='coding_started_at'
						) THEN
							ALTER TABLE daily_assignments ADD COLUMN coding_started_at TIMESTAMP WITH TIME ZONE;
						END IF;

						IF NOT EXISTS (
							SELECT 1 FROM information_schema.columns
							WHERE table_name='daily_assignments' AND column_name='coding_completed_at'
						) THEN
							ALTER TABLE daily_assignments ADD COLUMN coding_completed_at TIMESTAMP WITH TIME ZONE;
						END IF;

						IF NOT EXISTS (
							SELECT 1 FROM information_schema.columns
							WHERE table_name='daily_assignments' AND column_name='coding_time_spent_seconds'
						) THEN
							ALTER TABLE daily_assignments ADD COLUMN coding_time_spent_seconds INTEGER;
						END IF;

						IF NOT EXISTS (
							SELECT 1 FROM information_schema.columns
							WHERE table_name='daily_assignments' AND column_name='submission_attempts_count'
						) THEN
							ALTER TABLE daily_assignments ADD COLUMN submission_attempts_count INTEGER NOT NULL DEFAULT 0;
						END IF;
					END $$;
				""")
				)
				# Migrations for coding_questions columns
				conn.execute(
					text("""
					DO $$
					BEGIN
						IF NOT EXISTS (
							SELECT 1 FROM information_schema.columns
							WHERE table_name='coding_questions' AND column_name='function_name'
						) THEN
							ALTER TABLE coding_questions ADD COLUMN function_name VARCHAR(100) NOT NULL DEFAULT 'solve';
						END IF;

						IF NOT EXISTS (
							SELECT 1 FROM information_schema.columns
							WHERE table_name='coding_questions' AND column_name='parameter_definitions'
						) THEN
							ALTER TABLE coding_questions ADD COLUMN parameter_definitions JSON NOT NULL DEFAULT '[]';
						END IF;

						IF NOT EXISTS (
							SELECT 1 FROM information_schema.columns
							WHERE table_name='coding_questions' AND column_name='return_type'
						) THEN
							ALTER TABLE coding_questions ADD COLUMN return_type VARCHAR(50) NOT NULL DEFAULT 'int';
						END IF;

						IF NOT EXISTS (
							SELECT 1 FROM information_schema.columns
							WHERE table_name='coding_questions' AND column_name='starter_templates'
						) THEN
							ALTER TABLE coding_questions ADD COLUMN starter_templates JSON NOT NULL DEFAULT '{}';
						END IF;
					END $$;
				""")
				)
				conn.commit()
		except Exception as e:
			logger.warning("Database schema migration notice: %s", str(e))
