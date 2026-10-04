from __future__ import annotations

import json
import logging
from typing import Any, Literal, TypeVar

import httpx
from pydantic import BaseModel, Field, field_validator

from app.config import Config
from app.services.sanitizer import sanitize_text

logger: logging.Logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# ========================================================
# Pydantic Output Schemas
# ========================================================


class ExcelMappingResult(BaseModel):
	header_row_index: int = Field(description="Zero-indexed row number containing column headers")
	data_row_start_index: int = Field(
		description="Zero-indexed row number where student data rows begin"
	)
	column_mapping: dict[str, int] = Field(
		description="Mapping from standard fields ('name', 'roll_number', 'email', 'year_batch', 'section') to zero-indexed column index"
	)
	confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class TestCaseModel(BaseModel):
	input_data: str = Field(description="Standard input string. Must never be empty or whitespace.")
	expected_output: str = Field(description="Expected standard output string. Must never be empty or whitespace.")
	is_stress_case: bool = True

	@field_validator("input_data", "expected_output")
	@classmethod
	def validate_non_empty(cls, value: str) -> str:
		trimmed = str(value).strip()
		if not trimmed:
			raise ValueError("Test case input and output strings must never be empty or whitespace.")
		return trimmed


class StressTestCaseResult(BaseModel):
	test_cases: list[TestCaseModel]


class HardcodeReviewResult(BaseModel):
	status: Literal["clean", "flagged"]
	reason: str | None = None
	detected_shortcut: str | None = None


class MCQParsedItem(BaseModel):
	prompt_text: str = Field(description="The question prompt or statement")
	options: list[str] = Field(description="List of choice strings, minimum 2, usually 4")
	correct_option_index: int = Field(default=0, description="Zero-indexed correct option (0 for A, 1 for B, 2 for C, 3 for D)")
	explanation: str | None = Field(default=None, description="Explanation for the correct answer")
	difficulty: Literal["easy", "medium", "hard"] = Field(default="medium")


class MCQSheetParseResult(BaseModel):
	questions: list[MCQParsedItem]


class FullTestSuiteResult(BaseModel):
	sample_test_cases: list[TestCaseModel] = Field(description="3 sample test cases")
	hidden_test_cases: list[TestCaseModel] = Field(description="10 standard hidden test cases")


class CodingParsedItem(BaseModel):
	title: str = Field(description="Problem title")
	word_problem_text: str = Field(description="Problem statement, requirements, and input/output description")
	constraints_text: str = Field(default="1 <= N <= 10^5\nAll values within signed 32-bit integer limits.", description="Constraints")
	difficulty: Literal["easy", "medium", "hard"] = Field(default="medium")
	sample_test_cases: list[TestCaseModel] = Field(default_factory=list, description="Exactly 3 sample test cases")
	hidden_test_cases: list[TestCaseModel] = Field(default_factory=list, description="Exactly 10 standard hidden test cases")


class CodingSheetParseResult(BaseModel):
	questions: list[CodingParsedItem]


# ========================================================
# AI Client Service
# ========================================================


class AIClientService:
	"""
	Dual-mode LLM Client:
	1. If LLM_API_KEY is configured in .env, calls remote OpenAI-compatible endpoint.
	2. Falls back to local Ollama instance configured in .env.
	All responses are strictly parsed and validated against Pydantic V2 schemas.
	"""

	def __init__(self) -> None:
		self.remote_api_key: str | None = Config.LLM_API_KEY
		self.remote_base_url: str = Config.LLM_BASE_URL
		self.remote_model: str = Config.LLM_MODEL

		self.ollama_base_url: str = Config.OLLAMA_BASE_URL
		self.ollama_model: str = Config.OLLAMA_MODEL

	def _call_remote(self, system_prompt: str, user_prompt: str) -> str | None:
		if not self.remote_api_key:
			return None

		headers: dict[str, str] = {
			"Authorization": f"Bearer {self.remote_api_key}",
			"Content-Type": "application/json",
		}
		payload: dict[str, Any] = {
			"model": self.remote_model,
			"messages": [
				{"role": "system", "content": system_prompt},
				{"role": "user", "content": user_prompt},
			],
			"response_format": {"type": "json_object"},
			"temperature": 0.1,
		}

		try:
			with httpx.Client(timeout=45.0) as client:
				response: httpx.Response = client.post(
					f"{self.remote_base_url}/chat/completions",
					headers=headers,
					json=payload,
				)
				if response.status_code == 200:
					data: dict[str, Any] = response.json()
					content: str = data["choices"][0]["message"]["content"]
					return content
				else:
					logger.warning(
						"Remote LLM failed with status %d: %s", response.status_code, response.text
					)
					return None
		except Exception as e:
			logger.warning("Exception contacting remote LLM: %s. Falling back to Ollama.", str(e))
			return None

	def _call_ollama(self, system_prompt: str, user_prompt: str) -> str | None:
		payload: dict[str, Any] = {
			"model": self.ollama_model,
			"messages": [
				{"role": "system", "content": system_prompt},
				{"role": "user", "content": user_prompt},
			],
			"format": "json",
			"stream": False,
			"options": {"temperature": 0.1},
		}

		try:
			with httpx.Client(timeout=60.0) as client:
				response: httpx.Response = client.post(
					f"{self.ollama_base_url}/api/chat",
					json=payload,
				)
				if response.status_code == 200:
					data: dict[str, Any] = response.json()
					content: str = data["message"]["content"]
					return content
				else:
					logger.error(
						"Ollama LLM failed with status %d: %s", response.status_code, response.text
					)
					return None
		except Exception as e:
			logger.error("Exception contacting local Ollama: %s", str(e))
			return None

	def query_structured_json(
		self,
		system_prompt: str,
		user_prompt: str,
		schema_class: type[T],
		retry_on_invalid: bool = True,
	) -> T:
		"""
		Invokes LLM (remote first, local Ollama fallback), parses and validates
		the output against the specified Pydantic schema class.
		"""
		# Sanitize input prompts
		safe_system_prompt: str = sanitize_text(system_prompt, max_length=8192)
		safe_user_prompt: str = sanitize_text(user_prompt, max_length=16384)

		# 1. Try remote LLM
		raw_json: str | None = self._call_remote(safe_system_prompt, safe_user_prompt)

		# 2. Fall back to local Ollama if remote didn't succeed
		if not raw_json:
			raw_json = self._call_ollama(safe_system_prompt, safe_user_prompt)

		if not raw_json:
			raise RuntimeError(
				"Failed to obtain response from both remote LLM and local Ollama fallback."
			)

		# Parse and validate JSON
		try:
			parsed_data: dict[str, Any] = json.loads(raw_json)
			return schema_class.model_validate(parsed_data)
		except Exception as err:
			if retry_on_invalid:
				logger.warning(
					"Invalid LLM JSON response (%s). Retrying with stricter instructions...",
					str(err),
				)
				strict_system = (
					safe_system_prompt
					+ "\nCRITICAL: Return ONLY valid JSON matching the exact schema."
				)
				return self.query_structured_json(
					strict_system, safe_user_prompt, schema_class, retry_on_invalid=False
				)
			raise ValueError(
				f"LLM output could not be validated against schema {schema_class.__name__}: {err}"
			) from err

	# ========================================================
	# Specialized AI Tasks
	# ========================================================

	def infer_excel_mapping(self, sample_grid: list[list[str]]) -> ExcelMappingResult:
		"""Infer header row and column mapping from a sample Excel grid."""
		system_prompt = (
			"You are an expert Excel sheet schema analyzer. Given a tabular sample of rows from a college student roster, "
			"identify the header row and map the column indices to the standard fields:\n"
			"- name (student full name)\n"
			"- roll_number (unique student ID or registration number)\n"
			"- email (student email address)\n"
			"- year_batch (admission or graduation year, e.g. 2026)\n"
			"- section (class section, e.g. A, B)\n"
			"Return ONLY a JSON object conforming to the schema."
		)
		user_prompt = f"Excel Sample Grid:\n{json.dumps(sample_grid, ensure_ascii=False)}"
		return self.query_structured_json(system_prompt, user_prompt, ExcelMappingResult)

	def generate_stress_test_cases(
		self,
		title: str,
		problem_text: str,
		constraints_text: str,
		reference_solution: str | None = None,
	) -> StressTestCaseResult:
		"""Generate 10 standard validation hidden test cases for a coding problem."""
		system_prompt = (
			"You are an automated competitive programming test-case generator. "
			"Generate exactly 10 standard validation hidden test cases that strictly adhere to the problem constraints. "
			"These must be normal, valid test cases that thoroughly test the algorithm within standard constraints—NOT obscure or trick edge cases. "
			"Do NOT use HTML entities (use plain '<', '<=', '>', '>='). "
			"CRITICAL REQUIREMENT: Neither 'input_data' nor 'expected_output' must ever be empty, blank, or whitespace-only strings. "
			"Every test case must contain non-empty, valid standard input and expected output. "
			"Return a JSON object containing a list of 10 test cases with 'input_data' and 'expected_output'."
		)
		user_prompt = (
			f"Problem Title: {title}\nStatement: {problem_text}\nConstraints: {constraints_text}\n"
		)
		if reference_solution:
			user_prompt += f"Reference Solution Code:\n{reference_solution}\n"

		return self.query_structured_json(system_prompt, user_prompt, StressTestCaseResult)

	def generate_full_test_suite(
		self,
		title: str,
		problem_text: str,
		constraints_text: str,
		reference_solution: str | None = None,
	) -> FullTestSuiteResult:
		"""Generate exactly 3 sample test cases and 10 normal hidden test cases separated in JSON."""
		system_prompt = (
			"You are an automated competitive programming test-case generator. "
			"Generate a complete test suite for the coding problem with two separate lists:\n"
			"1. sample_test_cases: Exactly 3 clear, representative sample test cases for students to see in the problem description.\n"
			"2. hidden_test_cases: Exactly 10 standard validation hidden test cases adhering to problem constraints. "
			"These must be normal, regular test cases—NOT trick or obscure edge cases.\n"
			"Do NOT use HTML entities (use plain '<', '<=', '>', '>='). "
			"CRITICAL REQUIREMENT: Neither 'input_data' nor 'expected_output' must ever be empty, blank, or whitespace-only strings. "
			"Return ONLY a JSON object conforming to the FullTestSuiteResult schema."
		)
		user_prompt = (
			f"Problem Title: {title}\nStatement: {problem_text}\nConstraints: {constraints_text}\n"
		)
		if reference_solution:
			user_prompt += f"Reference Solution Code:\n{reference_solution}\n"

		return self.query_structured_json(system_prompt, user_prompt, FullTestSuiteResult)

	def review_code_for_hardcoding(
		self,
		problem_title: str,
		problem_text: str,
		student_code: str,
		sample_cases: list[dict[str, str]],
	) -> HardcodeReviewResult:
		"""Review passed student code to detect hardcoded outputs or lookup shortcuts."""
		system_prompt = (
			"You are an automated academic integrity auditor for a coding platform. "
			"Analyze the student's source code against the problem statement and sample test cases. "
			"Determine if the student hardcoded answers (e.g. if input == 'abc': print('xyz'), "
			"or printing constant values, or lookup table mapping only the given sample cases). "
			"Return 'clean' if the solution uses a general algorithmic approach, or 'flagged' if suspicious."
		)
		user_prompt = (
			f"Problem: {problem_title}\n"
			f"Description: {problem_text}\n"
			f"Sample Test Cases: {json.dumps(sample_cases)}\n"
			f"Student Source Code:\n{student_code}\n"
		)
		return self.query_structured_json(system_prompt, user_prompt, HardcodeReviewResult)

	def parse_mcq_sheet(self, sample_grid: list[list[str]]) -> MCQSheetParseResult:
		"""Analyze spreadsheet rows containing multiple-choice questions and extract structured items."""
		system_prompt = (
			"You are an expert educational spreadsheet parser. Analyze the given spreadsheet rows containing aptitude or computer science MCQs. "
			"Extract all valid questions. For each question, extract:\n"
			"- prompt_text: The full question statement\n"
			"- options: List of choices [Option A, Option B, Option C, Option D]\n"
			"- correct_option_index: Integer index of correct option (0 for A, 1 for B, 2 for C, 3 for D)\n"
			"- explanation: Explanation string if provided\n"
			"- difficulty: 'easy', 'medium', or 'hard'\n"
			"Return ONLY a JSON object conforming to the MCQSheetParseResult schema."
		)
		user_prompt = f"Spreadsheet Rows:\n{json.dumps(sample_grid, ensure_ascii=False)}"
		return self.query_structured_json(system_prompt, user_prompt, MCQSheetParseResult)

	def parse_coding_sheet(self, sample_grid: list[list[str]]) -> CodingSheetParseResult:
		"""Analyze spreadsheet rows containing coding challenges and extract structured items."""
		system_prompt = (
			"You are an expert competitive programming spreadsheet parser. Analyze the given spreadsheet rows containing coding problems. "
			"Extract all valid programming challenges. For each challenge, extract:\n"
			"- title: Problem title\n"
			"- word_problem_text: Problem statement, requirements, and input/output format specifications\n"
			"- constraints_text: Plain text constraints with mathematical inequalities (e.g. 1 <= N <= 10^5). Do NOT use HTML entities (use '<', '<=', '>', '>=' instead of '&lt;' or '&gt;').\n"
			"- difficulty: 'easy', 'medium', or 'hard'\n"
			"- sample_test_cases: List of exactly 3 representative sample test cases with 'input_data' and 'expected_output' to be visible to students in the problem description.\n"
			"- hidden_test_cases: List of exactly 10 standard validation hidden test cases with 'input_data' and 'expected_output'. These must be normal test cases covering regular inputs within constraints—NOT obscure or trick edge cases.\n"
			"CRITICAL REQUIREMENT: Neither 'input_data' nor 'expected_output' must ever be empty, blank, or whitespace-only strings. "
			"Return ONLY a JSON object conforming to the CodingSheetParseResult schema with 'sample_test_cases' and 'hidden_test_cases' as separate lists."
		)
		user_prompt = f"Spreadsheet Rows:\n{json.dumps(sample_grid, ensure_ascii=False)}"
		return self.query_structured_json(system_prompt, user_prompt, CodingSheetParseResult)


ai_service: AIClientService = AIClientService()

