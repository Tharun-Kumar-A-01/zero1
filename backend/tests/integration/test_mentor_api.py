from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from flask.testing import FlaskClient

from app.database import get_db_session
from app.models.enums import AssignmentStatus, DifficultyLevel, QuestionSetStatus
from app.models.mentor import MentorAssignment
from app.models.question import QuestionSet
from app.models.user import User


def test_mentor_question_crud(client: FlaskClient, admin_auth_headers: dict[str, str], test_admin_user: User) -> None:
	"""Test creating, updating, and deleting MCQs and Coding problems in draft status."""
	today = date.today()

	# Create active rotation and question set for test_admin_user
	with get_db_session() as session:
		rot = MentorAssignment(
			user_id=test_admin_user.id,
			week_start_date=today - timedelta(days=1),
			week_end_date=today + timedelta(days=5),
			status=AssignmentStatus.ACTIVE,
			created_by_admin_id=test_admin_user.id,
		)
		session.add(rot)
		session.flush()

		q_set = QuestionSet(
			mentor_assignment_id=rot.id,
			week_start_date=rot.week_start_date,
			status=QuestionSetStatus.DRAFT,
		)
		session.add(q_set)
		session.flush()
		q_set_id = q_set.id

	# 1. Add MCQ
	mcq_payload = {
		"question_set_id": q_set_id,
		"prompt_text": "What is the time complexity of binary search?",
		"options": ["O(N)", "O(log N)", "O(N^2)", "O(1)"],
		"correct_option_index": 1,
		"explanation": "Binary search divides the search space in half each step.",
		"difficulty": "easy",
	}
	res_mcq = client.post("/api/mentor/questions/mcq", json=mcq_payload, headers=admin_auth_headers)
	assert res_mcq.status_code == 200
	mcq_data: dict[str, Any] = res_mcq.get_json()
	assert mcq_data["success"] is True
	mcqs = mcq_data["data"]["mcqs"]
	assert len(mcqs) == 1
	mcq_id: int = mcqs[0]["id"]
	assert mcqs[0]["prompt_text"] == "What is the time complexity of binary search?"

	# 2. Update MCQ
	update_mcq_payload = {
		"prompt_text": "What is the worst-case time complexity of binary search?",
		"options": ["O(N)", "O(log N)", "O(N log N)", "O(1)"],
		"correct_option_index": 1,
		"difficulty": "medium",
	}
	res_update_mcq = client.put(f"/api/mentor/questions/mcq/{mcq_id}", json=update_mcq_payload, headers=admin_auth_headers)
	assert res_update_mcq.status_code == 200
	updated_mcq_data: dict[str, Any] = res_update_mcq.get_json()
	assert updated_mcq_data["success"] is True
	assert updated_mcq_data["data"]["mcqs"][0]["difficulty"] == DifficultyLevel.MEDIUM.value

	# 3. Add Coding Question (requires 3 sample + 10 hidden test cases separated in JSON)
	coding_payload = {
		"question_set_id": q_set_id,
		"title": "Two Sum",
		"word_problem_text": "Given an array of integers, return indices of two numbers that add up to target.",
		"constraints_text": "2 <= N <= 10^4",
		"difficulty": "easy",
		"sample_test_cases": [
			{"input": "4\n2 7 11 15\n9", "expected_output": "0 1"},
			{"input": "3\n3 2 4\n6", "expected_output": "1 2"},
			{"input": "2\n3 3\n6", "expected_output": "0 1"},
		],
		"hidden_test_cases": [
			{"input": "4\n-1 -2 -3 -4\n-6", "expected_output": "1 3"},
			{"input": "2\n0 4\n4", "expected_output": "0 1"},
			{"input": "2\n-3 3\n0", "expected_output": "0 1"},
			{"input": "3\n1 5 9\n10", "expected_output": "0 2"},
			{"input": "3\n1 2 3\n5", "expected_output": "1 2"},
			{"input": "4\n10 20 30 40\n50", "expected_output": "1 2"},
			{"input": "2\n100 200\n300", "expected_output": "0 1"},
			{"input": "3\n-10 -20 30\n10", "expected_output": "1 2"},
			{"input": "2\n0 0\n0", "expected_output": "0 1"},
			{"input": "4\n5 1 4 8\n9", "expected_output": "1 3"},
		],
	}
	res_coding = client.post("/api/mentor/questions/coding", json=coding_payload, headers=admin_auth_headers)
	assert res_coding.status_code == 200
	coding_data: dict[str, Any] = res_coding.get_json()
	assert coding_data["success"] is True
	coding_questions = coding_data["data"]["coding_questions"]
	assert len(coding_questions) == 1
	coding_id: int = coding_questions[0]["id"]
	assert coding_questions[0]["title"] == "Two Sum"
	assert coding_questions[0]["constraints_text"] == "2 &lt;= N &lt;= 10^4"
	assert len(coding_questions[0]["sample_test_cases"]) == 3
	assert len(coding_questions[0]["hidden_test_cases"]) == 10
	assert len(coding_questions[0]["all_test_cases"]) == 13

	# 4. Update Coding Question
	update_coding_payload = {
		"title": "Two Sum Target Match",
		"word_problem_text": "Return 0-indexed indices of the pair adding to target.",
		"difficulty": "medium",
	}
	res_update_coding = client.put(f"/api/mentor/questions/coding/{coding_id}", json=update_coding_payload, headers=admin_auth_headers)
	assert res_update_coding.status_code == 200
	updated_coding_data = res_update_coding.get_json()
	assert updated_coding_data["success"] is True
	assert updated_coding_data["data"]["coding_questions"][0]["title"] == "Two Sum Target Match"

	# 5. Delete MCQ
	res_del_mcq = client.delete(f"/api/mentor/questions/mcq/{mcq_id}", headers=admin_auth_headers)
	assert res_del_mcq.status_code == 200
	del_mcq_data = res_del_mcq.get_json()
	assert del_mcq_data["success"] is True
	assert len(del_mcq_data["data"]["mcqs"]) == 0

	# 6. Delete Coding Question
	res_del_coding = client.delete(f"/api/mentor/questions/coding/{coding_id}", headers=admin_auth_headers)
	assert res_del_coding.status_code == 200
	del_coding_data = res_del_coding.get_json()
	assert del_coding_data["success"] is True
	assert len(del_coding_data["data"]["coding_questions"]) == 0


def test_unassigned_mentor_draft_flow(
	client: FlaskClient,
	mentor_auth_headers: dict[str, str],
	admin_auth_headers: dict[str, str],
	test_mentor_user: User,
) -> None:
	"""Verify that a mentor with NO schedule can author questions in draft and publish once assigned."""
	# 1. Mentor checks their question set before having any schedule
	res_get = client.get("/api/mentor/question-set/my-week", headers=mentor_auth_headers)
	assert res_get.status_code == 200
	get_data = res_get.get_json()
	assert get_data["success"] is True
	assert get_data["data"] is not None
	assert get_data["data"]["status"] == "draft"
	assert get_data["data"]["mentor_assignment_id"] is None
	assert get_data["data"]["week_start_date"] is None
	qs_id = get_data["data"]["id"]

	# 2. Mentor adds an MCQ without having a schedule
	mcq_payload = {
		"prompt_text": "What is Python list comprehension?",
		"options": ["A syntax for concise list creation", "A loop", "A dictionary", "A tuple"],
		"correct_option_index": 0,
		"difficulty": "easy",
	}
	res_mcq = client.post("/api/mentor/questions/mcq", json=mcq_payload, headers=mentor_auth_headers)
	assert res_mcq.status_code == 200
	assert len(res_mcq.get_json()["data"]["mcqs"]) == 1

	# 3. Mentor adds a coding problem without having a schedule
	coding_payload = {
		"title": "Reverse String",
		"word_problem_text": "Given a string, reverse it.",
		"constraints_text": "1 <= N <= 100",
		"difficulty": "easy",
		"sample_test_cases": [
			{"input": "hello", "expected_output": "olleh"},
			{"input": "world", "expected_output": "dlrow"},
			{"input": "a", "expected_output": "a"},
		],
		"hidden_test_cases": [
			{"input": "abc", "expected_output": "cba"},
			{"input": "racecar", "expected_output": "racecar"},
			{"input": "python", "expected_output": "nohtyp"},
			{"input": "code", "expected_output": "edoc"},
			{"input": "fast", "expected_output": "tsaf"},
			{"input": "12345", "expected_output": "54321"},
			{"input": "xyz", "expected_output": "zyx"},
			{"input": "ab", "expected_output": "ba"},
			{"input": "testing", "expected_output": "gnitset"},
			{"input": "palindrome", "expected_output": "emordnilap"},
		],
	}
	res_coding = client.post("/api/mentor/questions/coding", json=coding_payload, headers=mentor_auth_headers)
	assert res_coding.status_code == 200
	assert len(res_coding.get_json()["data"]["coding_questions"]) == 1

	# 4. Attempt to publish before being assigned to a schedule -> rejected
	res_pub = client.post("/api/mentor/question-set/publish", headers=mentor_auth_headers)
	assert res_pub.status_code == 400
	assert res_pub.get_json()["error"]["code"] == "NO_ROTATION_ASSIGNED"

	# 5. Admin assigns this mentor to a rotation
	today = date.today()
	days_ahead = (0 - today.weekday() + 7) % 7
	next_monday = today + timedelta(days=days_ahead if days_ahead > 0 else 7)
	next_saturday = next_monday + timedelta(days=5)
	assign_payload = {
		"user_id": test_mentor_user.id,
		"week_start_date": next_monday.isoformat(),
		"week_end_date": next_saturday.isoformat(),
	}
	res_schedule = client.post("/api/admin/mentors/schedule", json=assign_payload, headers=admin_auth_headers)
	assert res_schedule.status_code == 200
	assignment_id = res_schedule.get_json()["data"]["id"]

	# 6. Mentor checks question set again -> draft is linked to assignment with all questions intact
	res_get_assigned = client.get("/api/mentor/question-set/my-week", headers=mentor_auth_headers)
	assert res_get_assigned.status_code == 200
	assigned_qs_data = res_get_assigned.get_json()["data"]
	assert assigned_qs_data["id"] == qs_id
	assert assigned_qs_data["mentor_assignment_id"] == assignment_id
	assert assigned_qs_data["week_start_date"] == next_monday.isoformat()
	assert len(assigned_qs_data["mcqs"]) == 1
	assert len(assigned_qs_data["coding_questions"]) == 1

