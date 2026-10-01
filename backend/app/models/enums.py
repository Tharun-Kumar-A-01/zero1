import enum


class UserRole(enum.StrEnum):
	ADMIN = "admin"
	MENTOR = "mentor"
	STUDENT = "student"


class AssignmentStatus(enum.StrEnum):
	UPCOMING = "upcoming"
	ACTIVE = "active"
	COMPLETED = "completed"
	MISSED = "missed"


class QuestionSetStatus(enum.StrEnum):
	DRAFT = "draft"
	PUBLISHED = "published"
	ARCHIVED = "archived"


class DifficultyLevel(enum.StrEnum):
	EASY = "easy"
	MEDIUM = "medium"
	HARD = "hard"


class TestCaseSource(enum.StrEnum):
	__test__ = False
	MENTOR_MANUAL = "mentor_manual"
	MENTOR_CSV = "mentor_csv"
	AI_GENERATED = "ai_generated"


class DailyMCQStatus(enum.StrEnum):
	PENDING = "pending"
	CORRECT = "correct"
	INCORRECT = "incorrect"
	SKIPPED = "skipped"


class DailyCodingStatus(enum.StrEnum):
	PENDING = "pending"
	SOLVED = "solved"
	ATTEMPTED_UNSOLVED = "attempted_unsolved"
	SKIPPED = "skipped"


class ExecutionStatus(enum.StrEnum):
	QUEUED = "queued"
	RUNNING = "running"
	PASSED = "passed"
	FAILED = "failed"
	TIMEOUT = "timeout"
	MEMORY_EXCEEDED = "memory_exceeded"
	COMPILATION_ERROR = "compilation_error"
	ERROR = "error"


class AIReviewStatus(enum.StrEnum):
	PENDING = "pending"
	CLEAN = "clean"
	FLAGGED = "flagged"
	ERROR = "error"


class MilestoneThresholdType(enum.StrEnum):
	STREAK_DAYS = "streak_days"
	TOTAL_POINTS = "total_points"
	PROBLEMS_SOLVED = "problems_solved"


class RewardType(enum.StrEnum):
	POINTS = "points"
	BADGE = "badge"
	CUSTOM = "custom"


class PointsReason(enum.StrEnum):
	DAILY_MCQ = "daily_mcq"
	DAILY_CODING = "daily_coding"
	MILESTONE = "milestone"
	MANUAL_ADJUSTMENT = "manual_adjustment"


class ImportJobStatus(enum.StrEnum):
	UPLOADED = "uploaded"
	PARSING = "parsing"
	AI_PARSED = "ai_parsed"
	AWAITING_CONFIRMATION = "awaiting_confirmation"
	CONFIRMED = "confirmed"
	COMMITTED = "committed"
	FAILED = "failed"
