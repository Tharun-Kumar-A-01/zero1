from __future__ import annotations

from datetime import date
from typing import Any

from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models.assignment import DailyAssignment
from app.models.enums import DailyCodingStatus, DailyMCQStatus
from app.models.user import User
from app.services.streak_service import evaluate_daily_streak_and_points


def test_streak_progression_consecutive_days(db: Session, test_student_user: User) -> None:
	day1: date = date(2026, 10, 1)
	day2: date = date(2026, 10, 2)

	# Day 1
	a1 = DailyAssignment(
		student_id=test_student_user.id,
		assignment_date=day1,
		mcq_status=DailyMCQStatus.CORRECT,
		coding_status=DailyCodingStatus.SOLVED,
	)
	db.add(a1)
	db.commit()

	with get_db_session() as s1:
		streak1, _, _ = evaluate_daily_streak_and_points(s1, test_student_user.id, day1)
		assert streak1 == 1

	# Day 2
	a2 = DailyAssignment(
		student_id=test_student_user.id,
		assignment_date=day2,
		mcq_status=DailyMCQStatus.CORRECT,
		coding_status=DailyCodingStatus.SOLVED,
	)
	db.add(a2)
	db.commit()

	with get_db_session() as s2:
		streak2, _, _ = evaluate_daily_streak_and_points(s2, test_student_user.id, day2)
		assert streak2 == 2


def test_streak_reset_after_missed_day(db: Session, test_student_user: User) -> None:
	day1: date = date(2026, 10, 1)
	day3: date = date(2026, 10, 3)  # Day 2 missed!

	# Day 1
	a1 = DailyAssignment(
		student_id=test_student_user.id,
		assignment_date=day1,
		mcq_status=DailyMCQStatus.CORRECT,
		coding_status=DailyCodingStatus.SOLVED,
	)
	db.add(a1)
	db.commit()

	with get_db_session() as s1:
		evaluate_daily_streak_and_points(s1, test_student_user.id, day1)

	# Day 3 (after a gap)
	a3 = DailyAssignment(
		student_id=test_student_user.id,
		assignment_date=day3,
		mcq_status=DailyMCQStatus.CORRECT,
		coding_status=DailyCodingStatus.SOLVED,
	)
	db.add(a3)
	db.commit()

	with get_db_session() as s3:
		streak3, _, _ = evaluate_daily_streak_and_points(s3, test_student_user.id, day3)
		assert streak3 == 1  # Streak reset back to 1


def test_oversized_code_rejection(
	client: FlaskClient, student_auth_headers: dict[str, str]
) -> None:
	huge_code: str = "x = 1\n" * 20000  # > 65KB
	res = client.post(
		"/api/student/daily/code-submit",
		headers=student_auth_headers,
		json={
			"assignment_id": 999999,
			"language": "python",
			"source_code": huge_code,
		},
	)
	assert res.status_code == 400
	data: dict[str, Any] = res.get_json()
	assert data["error"]["code"] == "SANITIZATION_FAILED"
