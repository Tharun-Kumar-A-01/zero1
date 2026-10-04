from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure test environment
os.environ["ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = (
	"super-secret-test-jwt-key-that-is-at-least-64-bytes-long-for-hmac-sha256"
)

from app import create_app
from app.database import Base, db_session
from app.models.enums import UserRole
from app.models.user import User

test_engine = create_engine(
	"sqlite:///:memory:",
	connect_args={"check_same_thread": False},
	poolclass=StaticPool,
)
TestSessionFactory = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
db_session.configure(bind=test_engine)


@pytest.fixture(scope="session")
def app() -> Generator[Flask, None, None]:
	"""Create and configure Flask application for testing."""
	app = create_app()
	app.config.update(
		{
			"TESTING": True,
			"JWT_SECRET_KEY": "super-secret-test-jwt-key-that-is-at-least-64-bytes-long-for-hmac-sha256",
		}
	)
	yield app


@pytest.fixture(autouse=True)
def init_and_clean_db() -> Generator[None, None, None]:
	"""Clean and recreate database tables before and after each test."""
	db_session.remove()
	Base.metadata.drop_all(bind=test_engine)
	Base.metadata.create_all(bind=test_engine)
	yield
	db_session.remove()
	Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(app: Flask) -> FlaskClient:
	"""Flask test client."""
	return app.test_client()


@pytest.fixture
def db(app: Flask) -> Generator[Session, None, None]:
	"""Database session for test setup and assertions."""
	session: Session = db_session()
	try:
		yield session
	finally:
		session.rollback()


@pytest.fixture
def test_admin_user(db: Session) -> User:
	"""Create a test admin user."""
	admin = User(
		name="Admin Tester",
		email="admin@test.edu",
		role=UserRole.ADMIN,
		is_active=True,
	)
	admin.set_password("AdminPass@123")
	db.add(admin)
	db.commit()
	return admin


@pytest.fixture
def test_student_user(db: Session) -> User:
	"""Create a test student user."""
	student = User(
		name="Student Tester",
		email="student@test.edu",
		role=UserRole.STUDENT,
		roll_number="STU001",
		year_batch="2026",
		department="CSE",
		section="A",
		is_active=True,
	)
	student.set_password("StudentPass@123")
	db.add(student)
	db.commit()
	return student


@pytest.fixture
def test_mentor_user(db: Session) -> User:
	"""Create a test mentor user."""
	mentor = User(
		name="Mentor Tester",
		email="mentor@test.edu",
		role=UserRole.MENTOR,
		is_active=True,
	)
	mentor.set_password("MentorPass@123")
	db.add(mentor)
	db.commit()
	return mentor


@pytest.fixture
def student_auth_headers(app: Flask, test_student_user: User) -> dict[str, str]:
	"""Generate Authorization headers for test student."""
	with app.app_context():
		token: str = create_access_token(
			identity=str(test_student_user.id),
			additional_claims={"role": "student", "name": test_student_user.name},
		)
		return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(app: Flask, test_admin_user: User) -> dict[str, str]:
	"""Generate Authorization headers for test admin."""
	with app.app_context():
		token: str = create_access_token(
			identity=str(test_admin_user.id),
			additional_claims={"role": "admin", "name": test_admin_user.name},
		)
		return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mentor_auth_headers(app: Flask, test_mentor_user: User) -> dict[str, str]:
	"""Generate Authorization headers for test mentor."""
	with app.app_context():
		token: str = create_access_token(
			identity=str(test_mentor_user.id),
			additional_claims={"role": "mentor", "name": test_mentor_user.name},
		)
		return {"Authorization": f"Bearer {token}"}
