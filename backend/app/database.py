from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, scoped_session, sessionmaker

from app.config import Config


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
	"""Create all registered database tables."""
	Base.metadata.create_all(bind=engine)
