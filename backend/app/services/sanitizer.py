from __future__ import annotations

import re
import unicodedata

import bleach


class SanitizationError(Exception):
	"""Raised when input fails strict sanitization requirements."""

	pass


# Regex to match invisible characters, zero-width chars, and non-printable control characters
INVISIBLE_CHARS_PATTERN: re.Pattern[str] = re.compile(
	r"[\u200B-\u200D\uFEFF\u200E\u200F\u202A-\u202E\u2066-\u2069\x00-\x08\x0B\x0C\x0E-\x1F\x7F]"
)

# Regex to completely remove script and style blocks including their contents
SCRIPT_STYLE_PATTERN: re.Pattern[str] = re.compile(
	r"<(script|style)[^>]*?>.*?</\1>", re.DOTALL | re.IGNORECASE
)

# Allowed tags and attributes for markdown/problem statements
ALLOWED_HTML_TAGS: list[str] = [
	"p",
	"br",
	"b",
	"i",
	"strong",
	"em",
	"code",
	"pre",
	"h1",
	"h2",
	"h3",
	"h4",
	"ul",
	"ol",
	"li",
	"blockquote",
	"table",
	"thead",
	"tbody",
	"tr",
	"th",
	"td",
	"hr",
]
ALLOWED_HTML_ATTRIBUTES: dict[str, list[str]] = {
	"code": ["class"],
	"th": ["align"],
	"td": ["align"],
}


def sanitize_text(raw_text: str, max_length: int = 16384, allow_html: bool = False) -> str:
	"""
	Sanitize general user text:
	1. Normalize Unicode using NFKC.
	2. Strip script/style blocks and dangerous tags.
	3. Strip zero-width, non-printing, and bidi control characters.
	4. Clean or strip HTML tags via bleach.
	5. Enforce strict max length bound.
	"""
	if not raw_text:
		return ""

	if len(raw_text) > max_length:
		raise SanitizationError(f"Input exceeds maximum allowed length of {max_length} characters.")

	# 1. NFKC normalization
	normalized: str = unicodedata.normalize("NFKC", raw_text)

	# 2. Strip script and style blocks entirely along with their inner contents
	without_scripts: str = SCRIPT_STYLE_PATTERN.sub("", normalized)

	# 3. Strip invisible and dangerous control characters
	cleaned: str = INVISIBLE_CHARS_PATTERN.sub("", without_scripts)

	# 4. HTML sanitization
	if allow_html:
		sanitized_html: str = bleach.clean(
			cleaned, tags=ALLOWED_HTML_TAGS, attributes=ALLOWED_HTML_ATTRIBUTES, strip=True
		)
		return sanitized_html.strip()

	# Completely strip all HTML tags for pure text fields
	stripped_text: str = bleach.clean(cleaned, tags=[], strip=True)
	return stripped_text.strip()


def sanitize_code(source_code: str, max_bytes: int = 65536) -> str:
	"""
	Sanitize source code before static analysis or Judge0 execution:
	1. Normalize Unicode to prevent homoglyph evasion.
	2. Strip invisible control characters while strictly preserving tabs, newlines, and carriage returns.
	3. Enforce maximum byte size limit.
	"""
	if not source_code:
		raise SanitizationError("Submitted code cannot be empty.")

	encoded_bytes: bytes = source_code.encode("utf-8")
	if len(encoded_bytes) > max_bytes:
		raise SanitizationError(
			f"Source code exceeds maximum size of {max_bytes} bytes ({len(encoded_bytes)} bytes received)."
		)

	# NFKC normalization
	normalized: str = unicodedata.normalize("NFKC", source_code)

	# Remove invisible and invalid control characters
	cleaned_code: str = INVISIBLE_CHARS_PATTERN.sub("", normalized)

	if not cleaned_code.strip():
		raise SanitizationError("Source code contains only whitespace or invisible characters.")

	return cleaned_code
