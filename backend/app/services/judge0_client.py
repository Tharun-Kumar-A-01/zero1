from __future__ import annotations

import base64
import logging
import time
from typing import Any

import httpx

from app.config import Config
from app.models.enums import ExecutionStatus

logger: logging.Logger = logging.getLogger(__name__)

# Standard Judge0 Language IDs
LANGUAGE_ID_MAP: dict[str, int] = {
	"python": 71,  # Python 3
	"python3": 71,
	"py": 71,
	"cpp": 54,  # C++ (GCC 9.2.0)
	"c++": 54,
	"java": 62,  # Java (OpenJDK 13.0.1)
	"c": 50,  # C (GCC 9.2.0)
}


def _b64encode_str(val: str | None) -> str | None:
	if val is None:
		return None
	return base64.b64encode(val.encode("utf-8")).decode("utf-8")


def _b64decode_str(val: str | None) -> str | None:
	if not val:
		return None
	try:
		return base64.b64decode(val.encode("utf-8")).decode("utf-8", errors="replace")
	except Exception:
		return val


class Judge0ExecutionResult:
	def __init__(
		self,
		status: ExecutionStatus,
		stdout: str | None,
		stderr: str | None,
		compile_output: str | None,
		time_ms: int | None,
		memory_kb: int | None,
		token: str | None,
	) -> None:
		self.status: ExecutionStatus = status
		self.stdout: str | None = stdout
		self.stderr: str | None = stderr
		self.compile_output: str | None = compile_output
		self.time_ms: int | None = time_ms
		self.memory_kb: int | None = memory_kb
		self.token: str | None = token

	def to_dict(self) -> dict[str, Any]:
		return {
			"status": self.status.value,
			"stdout": self.stdout,
			"stderr": self.stderr,
			"compile_output": self.compile_output,
			"time_ms": self.time_ms,
			"memory_kb": self.memory_kb,
			"token": self.token,
		}


class Judge0Client:
	"""Client wrapper for Judge0 code execution engine running in isolated container."""

	def __init__(self) -> None:
		self.base_url: str = Config.JUDGE0_URL
		self.auth_token: str | None = Config.JUDGE0_AUTH_TOKEN
		self.poll_timeout: int = Config.JUDGE0_POLL_TIMEOUT_SECONDS

	def _get_headers(self) -> dict[str, str]:
		headers: dict[str, str] = {
			"Content-Type": "application/json",
			"Accept": "application/json",
		}
		if self.auth_token:
			headers["X-Auth-Token"] = self.auth_token
		return headers

	def execute_submission(
		self,
		source_code: str,
		language: str,
		stdin: str = "",
		expected_output: str | None = None,
		cpu_time_limit: float = 2.0,
		memory_limit_kb: int = 128000,
	) -> Judge0ExecutionResult:
		"""
		Submits code strictly to Judge0 sandbox container, polls until completion or timeout,
		and returns standard ExecutionResult. Zero local fallbacks.
		"""
		normalized_lang: str = language.strip().lower()
		language_id: int | None = LANGUAGE_ID_MAP.get(normalized_lang)
		if language_id is None:
			return Judge0ExecutionResult(
				status=ExecutionStatus.ERROR,
				stdout=None,
				stderr=f"Unsupported language '{language}'",
				compile_output=None,
				time_ms=None,
				memory_kb=None,
				token=None,
			)

		payload: dict[str, Any] = {
			"source_code": _b64encode_str(source_code),
			"language_id": language_id,
			"stdin": _b64encode_str(stdin),
			"expected_output": _b64encode_str(expected_output),
			"cpu_time_limit": cpu_time_limit,
			"wall_time_limit": cpu_time_limit * 2.0,
			"memory_limit": memory_limit_kb,
			"max_processes_and_or_threads": 20,
			"enable_network": False,
			# Enforcing per-process/thread limits bypasses the cgroup v1 isolate requirement
			# allowing Judge0's Linux namespace sandbox to run cleanly on modern cgroup v2 hosts
			"enable_per_process_and_thread_time_limit": True,
			"enable_per_process_and_thread_memory_limit": True,
		}

		headers: dict[str, str] = self._get_headers()

		try:
			with httpx.Client(timeout=10.0) as client:
				# 1. Post submission (async / wait=false, base64 encoded)
				post_res: httpx.Response = client.post(
					f"{self.base_url}/submissions?base64_encoded=true&wait=false",
					headers=headers,
					json=payload,
				)
				if post_res.status_code not in (200, 201):
					logger.error(
						"Judge0 submission failed: %d - %s", post_res.status_code, post_res.text
					)
					return Judge0ExecutionResult(
						status=ExecutionStatus.ERROR,
						stdout=None,
						stderr=f"Judge0 error: HTTP {post_res.status_code} - {post_res.text}",
						compile_output=None,
						time_ms=None,
						memory_kb=None,
						token=None,
					)

				data: dict[str, Any] = post_res.json()
				token: str = data.get("token", "")

				# 2. Poll submission status
				start_time: float = time.time()
				while (time.time() - start_time) < self.poll_timeout:
					get_res: httpx.Response = client.get(
						f"{self.base_url}/submissions/{token}?base64_encoded=true",
						headers=headers,
					)
					if get_res.status_code == 200:
						status_data: dict[str, Any] = get_res.json()
						status_id: int = status_data.get("status", {}).get("id", 0)

						# 1: In Queue, 2: Processing
						if status_id in (1, 2):
							time.sleep(0.3)
							continue

						return self._map_judge0_response(status_data, token)

					time.sleep(0.5)

				# Timed out polling
				return Judge0ExecutionResult(
					status=ExecutionStatus.TIMEOUT,
					stdout=None,
					stderr="Judge0 execution response timed out while polling.",
					compile_output=None,
					time_ms=int(cpu_time_limit * 1000),
					memory_kb=None,
					token=token,
				)

		except Exception as exc:
			logger.error("Failed to execute code on Judge0 at %s: %s", self.base_url, str(exc))
			return Judge0ExecutionResult(
				status=ExecutionStatus.ERROR,
				stdout=None,
				stderr=f"Judge0 service unavailable: {exc}",
				compile_output=None,
				time_ms=None,
				memory_kb=None,
				token=None,
			)

	def _map_judge0_response(self, data: dict[str, Any], token: str) -> Judge0ExecutionResult:
		status_info: dict[str, Any] = data.get("status", {})
		status_id: int = status_info.get("id", 0)
		status_desc: str = status_info.get("description", "")
		stdout: str | None = _b64decode_str(data.get("stdout"))
		stderr: str | None = _b64decode_str(data.get("stderr"))
		compile_output: str | None = _b64decode_str(data.get("compile_output"))
		message: str | None = _b64decode_str(data.get("message"))

		time_val: str | float | None = data.get("time")
		time_ms: int | None = int(float(time_val) * 1000) if time_val is not None else None
		memory_kb: int | None = data.get("memory")

		if status_id == 3:  # Accepted
			exec_status = ExecutionStatus.PASSED
		elif status_id == 4:  # Wrong Answer
			exec_status = ExecutionStatus.FAILED
		elif status_id == 5:  # Time Limit Exceeded
			exec_status = ExecutionStatus.TIMEOUT
		elif status_id == 6:  # Compilation Error
			exec_status = ExecutionStatus.COMPILATION_ERROR
		elif status_id in (7, 8, 9, 10, 11, 12):  # Runtime Error or Memory Limit
			if (
				"memory" in str(stderr or "").lower()
				or "memory" in status_desc.lower()
			):
				exec_status = ExecutionStatus.MEMORY_EXCEEDED
			else:
				exec_status = ExecutionStatus.FAILED
		else:
			exec_status = ExecutionStatus.ERROR

		if not stderr and message:
			stderr = message
		elif not stderr and exec_status not in (ExecutionStatus.PASSED, ExecutionStatus.FAILED):
			stderr = status_desc or f"Execution stopped with status: {exec_status.value}"

		return Judge0ExecutionResult(
			status=exec_status,
			stdout=stdout,
			stderr=stderr,
			compile_output=compile_output,
			time_ms=time_ms,
			memory_kb=memory_kb,
			token=token,
		)


judge0_service: Judge0Client = Judge0Client()
