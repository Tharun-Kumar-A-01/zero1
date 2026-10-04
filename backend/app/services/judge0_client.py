from __future__ import annotations

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
	"""Client wrapper for Judge0 code execution engine."""

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
		Submit code to Judge0 sandbox, poll until completion or timeout,
		and return standard ExecutionResult.
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
			"source_code": source_code,
			"language_id": language_id,
			"stdin": stdin,
			"expected_output": expected_output,
			"cpu_time_limit": cpu_time_limit,
			"wall_time_limit": cpu_time_limit * 2.0,
			"memory_limit": memory_limit_kb,
			"max_processes_and_or_threads": 10,
			"enable_network": False,
		}

		headers: dict[str, str] = self._get_headers()

		try:
			with httpx.Client(timeout=10.0) as client:
				# 1. Post submission (async / wait=false)
				post_res: httpx.Response = client.post(
					f"{self.base_url}/submissions?base64_encoded=false&wait=false",
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
						stderr=f"Judge0 error: HTTP {post_res.status_code}",
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
						f"{self.base_url}/submissions/{token}?base64_encoded=false",
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
			logger.warning("Failed to connect to Judge0 at %s: %s. Checking fallback runner.", self.base_url, str(exc))
			if normalized_lang in ("python", "python3", "py"):
				return self._execute_python_local(source_code, stdin, expected_output, cpu_time_limit)

			return Judge0ExecutionResult(
				status=ExecutionStatus.ERROR,
				stdout=None,
				stderr=f"Judge0 execution sandbox unreachable at {self.base_url}: {exc}. Please verify Docker container 'judge0-server' is running.",
				compile_output=None,
				time_ms=None,
				memory_kb=None,
				token=None,
			)

	def _execute_python_local(
		self,
		source_code: str,
		stdin: str = "",
		expected_output: str | None = None,
		cpu_time_limit: float = 2.0,
	) -> Judge0ExecutionResult:
		"""Local subprocess runner for Python code when Judge0 sandbox is not running."""
		import subprocess
		import sys

		start_time: float = time.time()
		try:
			proc = subprocess.run(
				[sys.executable, "-c", source_code],
				input=stdin,
				capture_output=True,
				text=True,
				timeout=cpu_time_limit,
			)
			elapsed_ms: int = int((time.time() - start_time) * 1000)
			stdout_str: str = proc.stdout or ""
			stderr_str: str = proc.stderr or ""

			if proc.returncode != 0:
				is_syntax: bool = "SyntaxError" in stderr_str
				return Judge0ExecutionResult(
					status=ExecutionStatus.COMPILATION_ERROR if is_syntax else ExecutionStatus.FAILED,
					stdout=stdout_str,
					stderr=stderr_str,
					compile_output=stderr_str if is_syntax else None,
					time_ms=elapsed_ms,
					memory_kb=None,
					token=None,
				)

			passed: bool = True
			if expected_output is not None:
				norm_actual: str = "\n".join(line.rstrip() for line in stdout_str.strip().splitlines())
				norm_expected: str = "\n".join(line.rstrip() for line in expected_output.strip().splitlines())
				passed = (norm_actual == norm_expected)

			return Judge0ExecutionResult(
				status=ExecutionStatus.PASSED if passed else ExecutionStatus.FAILED,
				stdout=stdout_str,
				stderr=stderr_str if (not passed and stderr_str) else None,
				compile_output=None,
				time_ms=elapsed_ms,
				memory_kb=None,
				token=None,
			)
		except subprocess.TimeoutExpired:
			return Judge0ExecutionResult(
				status=ExecutionStatus.TIMEOUT,
				stdout=None,
				stderr=f"Time Limit Exceeded: Execution took longer than {cpu_time_limit:.1f} seconds.",
				compile_output=None,
				time_ms=int(cpu_time_limit * 1000),
				memory_kb=None,
				token=None,
			)
		except Exception as sub_exc:
			return Judge0ExecutionResult(
				status=ExecutionStatus.ERROR,
				stdout=None,
				stderr=f"Local execution error: {sub_exc}",
				compile_output=None,
				time_ms=None,
				memory_kb=None,
				token=None,
			)

	def _map_judge0_response(self, data: dict[str, Any], token: str) -> Judge0ExecutionResult:
		status_info: dict[str, Any] = data.get("status", {})
		status_id: int = status_info.get("id", 0)
		status_desc: str = status_info.get("description", "")
		stdout: str | None = data.get("stdout")
		stderr: str | None = data.get("stderr")
		compile_output: str | None = data.get("compile_output")

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

		if not stderr and exec_status not in (ExecutionStatus.PASSED, ExecutionStatus.FAILED):
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
