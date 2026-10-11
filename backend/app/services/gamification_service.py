from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.assignment import DailyAssignment
from app.models.enums import (
	DailyCodingStatus,
	DailyMCQStatus,
	MilestoneThresholdType,
	PointsReason,
	RewardType,
	UserRole,
)
from app.models.gamification import Milestone, PointsLedger, Reward, Streak, StudentReward
from app.models.user import User
from app.services.streak_service import get_student_total_points

logger: logging.Logger = logging.getLogger(__name__)

DEFAULT_MILESTONES = [
	# XP Badges (Milestones)
	{
		"name": "Bronze Explorer",
		"description": "Accumulate 100 total experience points across daily challenges.",
		"threshold_type": MilestoneThresholdType.TOTAL_POINTS,
		"threshold_value": 100,
		"reward_type": RewardType.BADGE,
		"icon": "gem_amber",
		"points_value": 10,
	},
	{
		"name": "Silver Solver",
		"description": "Accumulate 250 total experience points.",
		"threshold_type": MilestoneThresholdType.TOTAL_POINTS,
		"threshold_value": 250,
		"reward_type": RewardType.BADGE,
		"icon": "gem_sapphire",
		"points_value": 25,
	},
	{
		"name": "Gold Apprentice",
		"description": "Accumulate 500 total experience points.",
		"threshold_type": MilestoneThresholdType.TOTAL_POINTS,
		"threshold_value": 500,
		"reward_type": RewardType.BADGE,
		"icon": "star_gold",
		"points_value": 50,
	},
	{
		"name": "Emerald Champion",
		"description": "Accumulate 750 total experience points.",
		"threshold_type": MilestoneThresholdType.TOTAL_POINTS,
		"threshold_value": 750,
		"reward_type": RewardType.BADGE,
		"icon": "gem_emerald",
		"points_value": 75,
	},
	{
		"name": "Ruby Master",
		"description": "Accumulate 1000 total experience points and attain Grandmaster status.",
		"threshold_type": MilestoneThresholdType.TOTAL_POINTS,
		"threshold_value": 1000,
		"reward_type": RewardType.BADGE,
		"icon": "gem_ruby",
		"points_value": 100,
	},
	{
		"name": "Diamond Legend",
		"description": "Accumulate 2000 total experience points. True collegiate elite.",
		"threshold_type": MilestoneThresholdType.TOTAL_POINTS,
		"threshold_value": 2000,
		"reward_type": RewardType.BADGE,
		"icon": "gem_diamond",
		"points_value": 200,
	},
	# Streak Badges
	{
		"name": "3-Day Flame",
		"description": "Maintain active practice consistency for 3 consecutive days.",
		"threshold_type": MilestoneThresholdType.STREAK_DAYS,
		"threshold_value": 3,
		"reward_type": RewardType.BADGE,
		"icon": "flame",
		"points_value": 15,
	},
	{
		"name": "Week Warrior",
		"description": "Hit a 7-day daily quest streak.",
		"threshold_type": MilestoneThresholdType.STREAK_DAYS,
		"threshold_value": 7,
		"reward_type": RewardType.BADGE,
		"icon": "shield",
		"points_value": 35,
	},
	{
		"name": "Consistency Titan",
		"description": "Maintain an uninterrupted 14-day daily practice streak.",
		"threshold_type": MilestoneThresholdType.STREAK_DAYS,
		"threshold_value": 14,
		"reward_type": RewardType.BADGE,
		"icon": "shield",
		"points_value": 70,
	},
	{
		"name": "Monthly Legend",
		"description": "Maintain an uninterrupted 30-day daily practice streak.",
		"threshold_type": MilestoneThresholdType.STREAK_DAYS,
		"threshold_value": 30,
		"reward_type": RewardType.BADGE,
		"icon": "trophy",
		"points_value": 150,
	},
	# Problems Solved Achievements
	{
		"name": "Problem Novice",
		"description": "Solve 5 practice problems (MCQs or coding challenges).",
		"threshold_type": MilestoneThresholdType.PROBLEMS_SOLVED,
		"threshold_value": 5,
		"reward_type": RewardType.BADGE,
		"icon": "sword",
		"points_value": 20,
	},
	{
		"name": "Problem Adept",
		"description": "Solve 20 practice problems across your daily quests.",
		"threshold_type": MilestoneThresholdType.PROBLEMS_SOLVED,
		"threshold_value": 20,
		"reward_type": RewardType.BADGE,
		"icon": "sword",
		"points_value": 50,
	},
	{
		"name": "Problem Conqueror",
		"description": "Solve 50 practice problems. Demonstrates exceptional problem-solving volume.",
		"threshold_type": MilestoneThresholdType.PROBLEMS_SOLVED,
		"threshold_value": 50,
		"reward_type": RewardType.BADGE,
		"icon": "trophy",
		"points_value": 100,
	},
]


def seed_default_milestones(session: Session, creator_id: int | None = None) -> list[Milestone]:
	"""Seed standard badges and achievements if none exist in the database."""
	existing = session.scalars(select(Milestone)).first()
	if existing is not None:
		return list(session.scalars(select(Milestone)).all())

	if creator_id is None:
		admin = session.scalars(select(User).where(User.role == UserRole.ADMIN)).first()
		creator_id = admin.id if admin else 1

	created_milestones: list[Milestone] = []
	for item in DEFAULT_MILESTONES:
		reward = Reward(
			type=item["reward_type"],
			name=item["name"],
			description=item["description"],
			icon_asset_ref=item["icon"],
			points_value=item["points_value"],
		)
		session.add(reward)
		session.flush()

		milestone = Milestone(
			name=item["name"],
			description=item["description"],
			threshold_type=item["threshold_type"],
			threshold_value=item["threshold_value"],
			reward_id=reward.id,
			created_by=creator_id,
			is_active=True,
		)
		session.add(milestone)
		session.flush()
		created_milestones.append(milestone)

	return created_milestones


def evaluate_student_milestones(session: Session, student_id: int) -> list[StudentReward]:
	"""Evaluate and award all qualified milestones and badges for a student."""
	seed_default_milestones(session)

	streak_rec = session.scalars(select(Streak).where(Streak.student_id == student_id)).first()
	current_streak = streak_rec.current_streak if streak_rec else 0
	longest_streak = streak_rec.longest_streak if streak_rec else 0
	effective_streak = max(current_streak, longest_streak)

	total_points = get_student_total_points(session, student_id)

	mcq_solved = (
		session.scalar(
			select(func.count(DailyAssignment.id)).where(
				DailyAssignment.student_id == student_id,
				DailyAssignment.mcq_status == DailyMCQStatus.CORRECT,
			)
		)
		or 0
	)
	coding_solved = (
		session.scalar(
			select(func.count(DailyAssignment.id)).where(
				DailyAssignment.student_id == student_id,
				DailyAssignment.coding_status == DailyCodingStatus.SOLVED,
			)
		)
		or 0
	)
	problems_solved = mcq_solved + coding_solved

	awarded_milestone_ids = set(
		session.scalars(
			select(StudentReward.milestone_id).where(
				StudentReward.student_id == student_id,
				StudentReward.milestone_id.is_not(None),
			)
		).all()
	)

	active_milestones = session.scalars(
		select(Milestone).where(Milestone.is_active.is_(True))
	).all()

	new_awards: list[StudentReward] = []
	for milestone in active_milestones:
		if milestone.id in awarded_milestone_ids:
			continue

		is_eligible = False
		if milestone.threshold_type == MilestoneThresholdType.STREAK_DAYS:
			is_eligible = effective_streak >= milestone.threshold_value
		elif milestone.threshold_type == MilestoneThresholdType.TOTAL_POINTS:
			is_eligible = total_points >= milestone.threshold_value
		elif milestone.threshold_type == MilestoneThresholdType.PROBLEMS_SOLVED:
			is_eligible = problems_solved >= milestone.threshold_value

		if is_eligible:
			reward_record = StudentReward(
				student_id=student_id,
				reward_id=milestone.reward_id,
				milestone_id=milestone.id,
			)
			session.add(reward_record)
			session.flush()

			# Grant bonus points if configured
			if milestone.reward and milestone.reward.points_value and milestone.reward.points_value > 0:
				ledger = PointsLedger(
					student_id=student_id,
					delta=milestone.reward.points_value,
					reason=PointsReason.MILESTONE,
					reference_id=milestone.id,
				)
				session.add(ledger)
				session.flush()

			new_awards.append(reward_record)
			awarded_milestone_ids.add(milestone.id)

	return new_awards


def get_all_milestones(session: Session) -> list[dict[str, Any]]:
	"""Return all milestones with reward information and recipient counts."""
	seed_default_milestones(session)
	milestones = session.scalars(select(Milestone).order_by(Milestone.threshold_value.asc())).all()

	results: list[dict[str, Any]] = []
	for m in milestones:
		earned_count = (
			session.scalar(
				select(func.count(StudentReward.id)).where(StudentReward.milestone_id == m.id)
			)
			or 0
		)
		d = m.to_dict()
		d["earned_count"] = earned_count
		if m.reward:
			d["icon"] = m.reward.icon_asset_ref
			d["points_value"] = m.reward.points_value or 0
			d["reward_type"] = m.reward.type.value
		else:
			d["icon"] = "gem_amber"
			d["points_value"] = 0
			d["reward_type"] = "badge"
		results.append(d)

	return results


def create_custom_milestone(
	session: Session,
	creator_id: int,
	name: str,
	description: str,
	threshold_type: MilestoneThresholdType,
	threshold_value: int,
	reward_type: RewardType = RewardType.BADGE,
	icon: str = "gem_ruby",
	points_value: int = 0,
) -> Milestone:
	"""Create a new customizable achievement or milestone badge."""
	reward = Reward(
		type=reward_type,
		name=name,
		description=description,
		icon_asset_ref=icon,
		points_value=points_value,
	)
	session.add(reward)
	session.flush()

	milestone = Milestone(
		name=name,
		description=description,
		threshold_type=threshold_type,
		threshold_value=threshold_value,
		reward_id=reward.id,
		created_by=creator_id,
		is_active=True,
	)
	session.add(milestone)
	session.flush()
	return milestone


def update_custom_milestone(
	session: Session,
	milestone_id: int,
	data: dict[str, Any],
) -> Milestone | None:
	"""Update milestone requirements and reward details."""
	milestone = session.get(Milestone, milestone_id)
	if not milestone:
		return None

	if "name" in data and str(data["name"]).strip():
		milestone.name = str(data["name"]).strip()
		if milestone.reward:
			milestone.reward.name = str(data["name"]).strip()

	if "description" in data:
		milestone.description = str(data["description"]).strip()
		if milestone.reward:
			milestone.reward.description = str(data["description"]).strip()

	if "threshold_type" in data:
		tt = str(data["threshold_type"]).lower()
		if tt in MilestoneThresholdType.__members__.values():
			milestone.threshold_type = MilestoneThresholdType(tt)

	if "threshold_value" in data:
		milestone.threshold_value = int(data["threshold_value"])

	if "is_active" in data:
		milestone.is_active = bool(data["is_active"])

	if milestone.reward:
		if "icon" in data and str(data["icon"]).strip():
			milestone.reward.icon_asset_ref = str(data["icon"]).strip()
		if "points_value" in data:
			milestone.reward.points_value = int(data["points_value"])
		if "reward_type" in data:
			rt = str(data["reward_type"]).lower()
			if rt in RewardType.__members__.values():
				milestone.reward.type = RewardType(rt)

	session.flush()
	return milestone


def delete_custom_milestone(session: Session, milestone_id: int) -> bool:
	"""Delete milestone and associated reward records."""
	milestone = session.get(Milestone, milestone_id)
	if not milestone:
		return False

	# Delete associated student rewards referencing this milestone
	session.execute(delete(StudentReward).where(StudentReward.milestone_id == milestone_id))

	reward_id = milestone.reward_id
	session.delete(milestone)
	session.flush()

	if reward_id:
		reward = session.get(Reward, reward_id)
		if reward:
			session.delete(reward)
			session.flush()

	return True
