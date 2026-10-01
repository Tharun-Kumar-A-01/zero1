import os
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

# Load .env file from project root or backend dir
backend_env_path: Path = Path(__file__).resolve().parent.parent / ".env"
root_env_path: Path = Path(__file__).resolve().parent.parent.parent / ".env"

if root_env_path.exists():
	load_dotenv(dotenv_path=root_env_path)
elif backend_env_path.exists():
	load_dotenv(dotenv_path=backend_env_path)


class Config:
	"""Application configuration loaded deterministically from environment."""

	ENV: str = os.getenv("ENV", "development")
	SECRET_KEY: str = os.getenv("SECRET_KEY", "default-dev-secret-key-change-in-production")
	JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "default-dev-jwt-secret-key")

	JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(
		minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "30"))
	)
	JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(
		days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "7"))
	)

	# Canonical Timezone (defaults to Asia/Kolkata)
	SYSTEM_TIMEZONE_STR: str = os.getenv("SYSTEM_TIMEZONE", "Asia/Kolkata")
	SYSTEM_TIMEZONE: ZoneInfo = ZoneInfo(SYSTEM_TIMEZONE_STR)

	# Database
	DATABASE_URL: str = os.getenv(
		"DATABASE_URL", "postgresql+psycopg2://postgres:postgrespassword@localhost:5432/zero1_db"
	)

	# Valkey / Cache / Rate Limiter / Broker
	VALKEY_URL: str = os.getenv("VALKEY_URL", "valkey://localhost:6379/0")
	CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "valkey://localhost:6379/0")
	CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "valkey://localhost:6379/0")
	RATE_LIMIT_STORAGE_URL: str = os.getenv("RATE_LIMIT_STORAGE_URL", "valkey://localhost:6379/1")

	# Initial Admin Seed
	INITIAL_ADMIN_EMAIL: str = os.getenv("INITIAL_ADMIN_EMAIL", "admin@dept.edu")
	INITIAL_ADMIN_PASSWORD: str = os.getenv("INITIAL_ADMIN_PASSWORD", "AdminPassword@123")
	INITIAL_ADMIN_NAME: str = os.getenv("INITIAL_ADMIN_NAME", "System Administrator")

	# Judge0
	JUDGE0_URL: str = os.getenv("JUDGE0_URL", "http://localhost:2358").rstrip("/")
	JUDGE0_AUTH_TOKEN: str | None = os.getenv("JUDGE0_AUTH_TOKEN") or None
	JUDGE0_POLL_TIMEOUT_SECONDS: int = int(os.getenv("JUDGE0_POLL_TIMEOUT_SECONDS", "10"))

	# LLM Settings (Primary & Local Fallback)
	LLM_API_KEY: str | None = os.getenv("LLM_API_KEY") or None
	LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
	LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

	OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
	OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

	# Platform Business Rules
	STREAK_REQUIRES_BOTH: bool = os.getenv("STREAK_REQUIRES_BOTH", "true").lower() == "true"
	GRACE_CUTOFF_HOURS: int = int(os.getenv("GRACE_CUTOFF_HOURS", "3"))
	MIN_MCQ_POOL_SIZE: int = int(os.getenv("MIN_MCQ_POOL_SIZE", "7"))
	MIN_CODING_POOL_SIZE: int = int(os.getenv("MIN_CODING_POOL_SIZE", "7"))
