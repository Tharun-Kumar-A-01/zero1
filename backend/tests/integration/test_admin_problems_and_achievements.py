from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from flask.testing import FlaskClient

from app.database import get_db_session
from app.models.enums import AssignmentStatus, QuestionSetStatus
from app.models.mentor import MentorAssignment
from app.models.question import QuestionSet
from app.models.user import User


def test_admin_problems_management(
	client: FlaskClient, admin_auth_headers: dict[str, str], test_admin_user: User
) -> None:
	"""Verify admin can list, create, publish, unpublish question sets and edit published questions."""
	# 1. Create a question set
	res = client.post(
		"/api/admin/question-sets",
		json={"status": "draft", "week_start_date": date.today().isoformat()},
		headers=admin_auth_headers,
	)
	assert res.status_code == 200
	qs_id = res.get_json()["data"]["id"]

	# 2. Add an MCQ to it
	mcq_res = client.post(
		"/api/mentor/questions/mcq",
		json={
			"question_set_id": qs_id,
			"prompt_text": "What is 2 + 2?",
			"options": ["3", "4", "5"],
			"correct_option_index": 1,
			"explanation": "Math basics",
		},
		headers=admin_auth_headers,
	)
	assert mcq_res.status_code == 200
	mcq_id = mcq_res.get_json()["data"]["mcqs"][0]["id"]

	# 3. Publish the question set
	pub_res = client.post(f"/api/admin/question-sets/{qs_id}/publish", headers=admin_auth_headers)
	assert pub_res.status_code == 200
	assert pub_res.get_json()["data"]["status"] == "published"

	# 4. Admin CAN edit the question even though it is PUBLISHED!
	edit_res = client.put(
		f"/api/mentor/questions/mcq/{mcq_id}",
		json={"prompt_text": "What is 2 + 2 in arithmetic?"},
		headers=admin_auth_headers,
	)
	assert edit_res.status_code == 200
	assert edit_res.get_json()["success"] is True

	# 5. Fetch active published problems
	active_res = client.get("/api/admin/problems/active", headers=admin_auth_headers)
	assert active_res.status_code == 200
	assert active_res.get_json()["data"]["id"] == qs_id

	# 6. Unpublish
	unpub_res = client.post(f"/api/admin/question-sets/{qs_id}/unpublish", headers=admin_auth_headers)
	assert unpub_res.status_code == 200
	assert unpub_res.get_json()["data"]["status"] == "draft"


def test_admin_achievements_management(
	client: FlaskClient, admin_auth_headers: dict[str, str], student_auth_headers: dict[str, str]
) -> None:
	"""Verify admin can create, update, list, and delete custom achievements."""
	# 1. List achievements (triggers default seed)
	list_res = client.get("/api/admin/achievements", headers=admin_auth_headers)
	assert list_res.status_code == 200
	achievements = list_res.get_json()["data"]
	assert len(achievements) >= 10

	# 2. Create custom achievement
	create_res = client.post(
		"/api/admin/achievements",
		json={
			"name": "Speed Demon",
			"description": "Solve 3 problems in record time.",
			"threshold_type": "problems_solved",
			"threshold_value": 3,
			"reward_type": "badge",
			"icon": "gem_ruby",
			"points_value": 50,
		},
		headers=admin_auth_headers,
	)
	assert create_res.status_code == 200
	new_ach = create_res.get_json()["data"]
	ach_id = new_ach["id"]
	assert new_ach["name"] == "Speed Demon"

	# 3. Update achievement
	update_res = client.put(
		f"/api/admin/achievements/{ach_id}",
		json={"threshold_value": 4, "points_value": 75},
		headers=admin_auth_headers,
	)
	assert update_res.status_code == 200
	assert update_res.get_json()["data"]["threshold_value"] == 4

	# 4. Student progress fetches earned badges
	prog_res = client.get("/api/student/progress", headers=student_auth_headers)
	assert prog_res.status_code == 200
	assert "badges" in prog_res.get_json()["data"]

	# 5. Delete achievement
	del_res = client.delete(f"/api/admin/achievements/{ach_id}", headers=admin_auth_headers)
	assert del_res.status_code == 200
	assert del_res.get_json()["success"] is True
