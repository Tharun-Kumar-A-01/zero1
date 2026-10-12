from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, g, request
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

# Determine log directory (default: backend/logs)
BACKEND_DIR: Path = Path(__file__).resolve().parent.parent.parent
LOGS_DIR: Path = BACKEND_DIR / "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

REQUESTS_LOG_PATH: Path = LOGS_DIR / "requests.log"
DATABASE_LOG_PATH: Path = LOGS_DIR / "database.log"
AI_AGENT_LOG_PATH: Path = LOGS_DIR / "ai_agent.log"
APP_LOG_PATH: Path = LOGS_DIR / "app.log"

SENSITIVE_KEYS: set[str] = {
	"password",
	"password_hash",
	"token",
	"access_token",
	"refresh_token",
	"jwt",
	"secret",
	"authorization",
}


def sanitize_payload(data: Any) -> Any:
	"""Recursively sanitize sensitive fields like passwords and tokens."""
	if isinstance(data, dict):
		sanitized: dict[str, Any] = {}
		for k, v in data.items():
			if k.lower() in SENSITIVE_KEYS:
				sanitized[k] = "***"
			else:
				sanitized[k] = sanitize_payload(v)
		return sanitized
	elif isinstance(data, list):
		return [sanitize_payload(item) for item in data]
	return data


def to_single_line(text: Any, max_length: int | None = 200) -> str:
	"""Convert any text/data into a clean, single-line string with escaped spaces."""
	if text is None:
		return ""
	s = str(text)
	flat = " ".join(s.split())
	if max_length and len(flat) > max_length:
		return flat[:max_length] + "..."
	return flat


# Set up file formatters and handlers
file_formatter = logging.Formatter(
	"%(asctime)s [%(levelname)s] [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
console_formatter = logging.Formatter("%(message)s")

# Console handler for clean single-line output
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(console_formatter)
console_handler.setLevel(logging.INFO)


def _create_file_handler(file_path: Path) -> logging.FileHandler:
	handler = logging.FileHandler(str(file_path), encoding="utf-8")
	handler.setFormatter(file_formatter)
	handler.setLevel(logging.INFO)
	return handler


# Specific loggers
req_logger = logging.getLogger("zero1.request")
req_logger.setLevel(logging.INFO)
req_logger.propagate = False
req_logger.addHandler(console_handler)
req_logger.addHandler(_create_file_handler(REQUESTS_LOG_PATH))
req_logger.addHandler(_create_file_handler(APP_LOG_PATH))

db_logger = logging.getLogger("zero1.database")
db_logger.setLevel(logging.INFO)
db_logger.propagate = False
db_logger.addHandler(console_handler)
db_logger.addHandler(_create_file_handler(DATABASE_LOG_PATH))
db_logger.addHandler(_create_file_handler(APP_LOG_PATH))

ai_logger = logging.getLogger("zero1.ai")
ai_logger.setLevel(logging.INFO)
ai_logger.propagate = False
ai_logger.addHandler(console_handler)
ai_logger.addHandler(_create_file_handler(AI_AGENT_LOG_PATH))
ai_logger.addHandler(_create_file_handler(APP_LOG_PATH))


# ========================================================
# 1. Incoming Request Logging
# ========================================================


def init_request_logging(app: Flask) -> None:
	"""Registers Flask before_request and after_request hooks for single-line console logging and file recording."""

	@app.before_request
	def _log_before_request() -> None:
		g._req_start_time = time.perf_counter()

		# Capture incoming payload
		body_repr: str = ""
		try:
			if request.is_json:
				json_data = request.get_json(silent=True)
				if json_data is not None:
					clean_json = sanitize_payload(json_data)
					body_repr = json.dumps(clean_json, ensure_ascii=False)
			elif request.form or request.files:
				form_dict = sanitize_payload(request.form.to_dict())
				files_list = [f"{k}:{v.filename}" for k, v in request.files.items()]
				body_repr = json.dumps({"form": form_dict, "files": files_list}, ensure_ascii=False)
			else:
				raw_data = request.get_data(as_text=True)
				if raw_data:
					body_repr = to_single_line(raw_data, max_length=150)
		except Exception as e:
			body_repr = f"<error parsing body: {e}>"

		g._req_body = body_repr

	@app.after_request
	def _log_after_request(response: Any) -> Any:
		try:
			start = getattr(g, "_req_start_time", None)
			duration_str = f"{(time.perf_counter() - start) * 1000:.1f}ms" if start else "0ms"
			body_str = getattr(g, "_req_body", "")

			ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1")
			if "," in ip:
				ip = ip.split(",")[0].strip()

			query = f"?{request.query_string.decode('utf-8')}" if request.query_string else ""
			status_code = response.status_code

			# Single-line message for console and file
			body_part = f" | Body: {to_single_line(body_str, max_length=200)}" if body_str else ""
			log_line = (
				f"[REQ] {request.method} {request.path}{query} -> {status_code} "
				f"({duration_str}) IP={ip}{body_part}"
			)
			req_logger.info(log_line)
		except Exception:
			pass
		return response


# ========================================================
# 2. Database Write Logging
# ========================================================


def _extract_model_changes(op: str, obj: Any) -> dict[str, Any]:
	"""Extract readable dictionary of attributes or changes for an ORM model."""
	data: dict[str, Any] = {}
	try:
		insp = inspect(obj)
		if op == "INSERT":
			for attr in insp.attrs:
				if attr.key.startswith("_") or attr.key in SENSITIVE_KEYS:
					continue
				val = getattr(obj, attr.key, None)
				if isinstance(val, (int, float, str, bool, type(None))):
					data[attr.key] = val
				elif hasattr(val, "value"):  # Enum
					data[attr.key] = val.value
				elif isinstance(val, (datetime,)):
					data[attr.key] = val.isoformat()
		elif op == "UPDATE":
			for attr in insp.attrs:
				if attr.key.startswith("_") or attr.key in SENSITIVE_KEYS:
					continue
				hist = attr.history
				if hist.has_changes():
					old_v = hist.deleted[0] if hist.deleted else None
					new_v = hist.added[0] if hist.added else None
					if hasattr(old_v, "value"):
						old_v = old_v.value
					if hasattr(new_v, "value"):
						new_v = new_v.value
					data[attr.key] = f"{old_v} -> {new_v}"
		elif op == "DELETE":
			data["identity"] = getattr(insp, "identity", None)
	except Exception:
		pass
	return data


_db_logging_initialized = False


def init_db_logging() -> None:
	"""Intercept all SQLAlchemy database write events (INSERT, UPDATE, DELETE)."""
	global _db_logging_initialized
	if _db_logging_initialized:
		return
	_db_logging_initialized = True

	@event.listens_for(Session, "after_flush")
	def _receive_after_flush(session: Session, flush_context: Any) -> None:
		try:
			for obj in list(session.new):
				_log_single_db_write("INSERT", obj)
			for obj in list(session.dirty):
				_log_single_db_write("UPDATE", obj)
			for obj in list(session.deleted):
				_log_single_db_write("DELETE", obj)
		except Exception:
			pass


def _log_single_db_write(op: str, obj: Any) -> None:
	"""Log a single database write in one line to console and record in log file."""
	try:
		model_name = obj.__class__.__name__
		table_name = getattr(obj, "__tablename__", model_name.lower())
		insp = inspect(obj)
		pk = insp.identity[0] if (insp and insp.identity) else getattr(obj, "id", None)
		changes = _extract_model_changes(op, obj)

		# Format single-line console output
		changes_str = to_single_line(json.dumps(changes, ensure_ascii=False, default=str), max_length=150)
		msg = f"[DB_WRITE] {op} {model_name} (table={table_name}, id={pk}) changes={changes_str}"
		db_logger.info(msg)
	except Exception:
		pass


# ========================================================
# 3. AI Agent Communication Logging
# ========================================================


def log_ai_prompt(
	task_name: str,
	system_prompt: str,
	user_prompt: str,
	model: str,
	provider: str = "remote",
) -> None:
	"""Log outgoing prompt sent to AI agent to file and single-line console."""
	try:
		flat_prompt = to_single_line(user_prompt, max_length=180)
		single_line = (
			f"[AI_PROMPT] task={task_name} provider={provider} model={model} prompt=\"{flat_prompt}\""
		)
		ai_logger.info(single_line)
	except Exception:
		pass


def log_ai_response(
	task_name: str,
	response_content: str | None,
	duration_ms: float,
	success: bool,
	model: str,
	provider: str = "remote",
) -> None:
	"""Log incoming response from AI agent to file and single-line console."""
	try:
		status = "SUCCESS" if success else "FAILED"
		flat_res = to_single_line(response_content, max_length=180) if response_content else "None"
		single_line = (
			f"[AI_RESPONSE] task={task_name} provider={provider} model={model} "
			f"status={status} ({duration_ms:.1f}ms) response=\"{flat_res}\""
		)
		ai_logger.info(single_line)
	except Exception:
		pass
