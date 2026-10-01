from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.services.ai_client import ExcelMappingResult, HardcodeReviewResult, StressTestCaseResult


def test_excel_mapping_schema_valid() -> None:
	payload = {
		"header_row_index": 0,
		"data_row_start_index": 1,
		"column_mapping": {"name": 0, "roll_number": 1, "email": 2},
		"confidence": 0.95,
	}
	model = ExcelMappingResult.model_validate(payload)
	assert model.header_row_index == 0
	assert model.column_mapping["email"] == 2
	assert model.confidence == 0.95


def test_excel_mapping_schema_invalid() -> None:
	# Missing required header_row_index
	payload = {"column_mapping": {"name": 0}}
	with pytest.raises(ValidationError):
		ExcelMappingResult.model_validate(payload)


def test_stress_test_case_schema() -> None:
	payload = {
		"test_cases": [
			{"input_data": "100000", "expected_output": "200000", "is_stress_case": True}
		]
	}
	model = StressTestCaseResult.model_validate(payload)
	assert len(model.test_cases) == 1
	assert model.test_cases[0].input_data == "100000"


def test_hardcode_review_schema_literals() -> None:
	clean_payload = {"status": "clean", "reason": "Standard recursion used"}
	model_clean = HardcodeReviewResult.model_validate(clean_payload)
	assert model_clean.status == "clean"

	flagged_payload = {"status": "flagged", "reason": "Lookup table of 5 inputs detected"}
	model_flagged = HardcodeReviewResult.model_validate(flagged_payload)
	assert model_flagged.status == "flagged"

	invalid_payload = {"status": "unknown"}
	with pytest.raises(ValidationError):
		HardcodeReviewResult.model_validate(invalid_payload)
