from __future__ import annotations

import pytest

from app.services.sanitizer import SanitizationError, sanitize_code, sanitize_text


def test_nfkc_normalization() -> None:
	# Ligature fi (\uFB01) should normalize to separate 'f' and 'i'
	raw_input: str = "De\ufb01nition"
	result: str = sanitize_text(raw_input)
	assert result == "Definition"


def test_invisible_char_removal() -> None:
	# Zero-width spaces, joiners, and bidi override chars
	raw_input: str = "Student\u200b Name\u200d\u202a"
	result: str = sanitize_text(raw_input)
	assert result == "Student Name"


def test_html_stripping_pure_text() -> None:
	raw_input: str = "Hello <script>alert(1)</script> World <b>bold</b>"
	result: str = sanitize_text(raw_input, allow_html=False)
	assert "<script>" not in result
	assert "alert(1)" not in result
	assert "<b>" not in result
	assert result == "Hello  World bold"


def test_html_whitelist_for_markdown() -> None:
	raw_input: str = "<p>Problem Statement</p><code>x = 10</code><script>evil()</script>"
	result: str = sanitize_text(raw_input, allow_html=True)
	assert "<p>Problem Statement</p>" in result
	assert "<code>x = 10</code>" in result
	assert "<script>" not in result


def test_max_length_enforcement() -> None:
	raw_input: str = "A" * 100
	with pytest.raises(SanitizationError, match="exceeds maximum allowed length"):
		sanitize_text(raw_input, max_length=50)


def test_code_sanitizer_preserves_tabs_and_newlines() -> None:
	code: str = "def solve():\n\treturn 42\n"
	result: str = sanitize_code(code)
	assert result == code
	assert "\t" in result
	assert "\n" in result


def test_code_sanitizer_rejects_empty_or_whitespace_only() -> None:
	with pytest.raises(SanitizationError):
		sanitize_code("")
	with pytest.raises(SanitizationError):
		sanitize_code("   \u200b\n\t  ")
