from __future__ import annotations

import ast
import re

# Globally banned Python modules
BANNED_PYTHON_MODULES: set[str] = {
	"os",
	"sys",
	"subprocess",
	"threading",
	"multiprocessing",
	"concurrent",
	"concurrent.futures",
	"socket",
	"requests",
	"urllib",
	"urllib3",
	"http",
	"http.client",
	"ftplib",
	"pty",
	"shutil",
	"importlib",
	"posix",
	"nt",
	"ctypes",
	"signal",
}

# Globally banned Python built-in function calls
BANNED_PYTHON_CALLS: set[str] = {
	"eval",
	"exec",
	"open",
	"__import__",
	"globals",
	"locals",
	"compile",
}

# C++ regex for forbidden constructs
CPP_FORBIDDEN_REGEX: re.Pattern[str] = re.compile(
	r"(#include\s*<(?:thread|future|sys/socket\.h|arpa/inet\.h|netdb\.h|unistd\.h)>)|"
	r"(\b(?:fork|system|popen|execve|pthread_create)\s*\()",
	re.IGNORECASE,
)

# Java regex for forbidden constructs
JAVA_FORBIDDEN_REGEX: re.Pattern[str] = re.compile(
	r"(\bjava\.(?:lang\.Thread|util\.concurrent|net\.|nio\.file\.)\b)|"
	r"(\bRuntime\.getRuntime\(\)\.exec\b)|"
	r"(\bProcessBuilder\b)",
	re.IGNORECASE,
)


class PythonSecurityVisitor(ast.NodeVisitor):
	"""AST visitor checking Python source for banned imports, function calls, and attributes."""

	def __init__(self, custom_forbidden: set[str]) -> None:
		self.violations: list[str] = []
		self.custom_forbidden: set[str] = custom_forbidden

	def visit_Import(self, node: ast.Import) -> None:
		for alias in node.names:
			root_mod: str = alias.name.split(".")[0]
			if alias.name in BANNED_PYTHON_MODULES or root_mod in BANNED_PYTHON_MODULES:
				self.violations.append(f"Importing module '{alias.name}' is strictly prohibited.")
			if alias.name in self.custom_forbidden:
				self.violations.append(f"Forbidden construct '{alias.name}' detected.")
		self.generic_visit(node)

	def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
		if node.module:
			root_mod: str = node.module.split(".")[0]
			if node.module in BANNED_PYTHON_MODULES or root_mod in BANNED_PYTHON_MODULES:
				self.violations.append(
					f"Importing from module '{node.module}' is strictly prohibited."
				)
			if node.module in self.custom_forbidden:
				self.violations.append(f"Forbidden construct '{node.module}' detected.")
		for alias in node.names:
			if alias.name in BANNED_PYTHON_CALLS:
				self.violations.append(f"Importing '{alias.name}' is prohibited.")
			if alias.name in self.custom_forbidden:
				self.violations.append(f"Forbidden construct '{alias.name}' detected.")
		self.generic_visit(node)

	def visit_Call(self, node: ast.Call) -> None:
		# Check direct calls like eval(...), open(...)
		if isinstance(node.func, ast.Name):
			if node.func.id in BANNED_PYTHON_CALLS:
				self.violations.append(f"Direct call to '{node.func.id}()' is prohibited.")
			if node.func.id in self.custom_forbidden:
				self.violations.append(f"Forbidden construct '{node.func.id}' detected.")
		self.generic_visit(node)

	def visit_Attribute(self, node: ast.Attribute) -> None:
		if node.attr in {"__builtins__", "__subclasses__", "__bases__"}:
			self.violations.append(f"Accessing reflection attribute '{node.attr}' is prohibited.")
		self.generic_visit(node)


def analyze_student_code(
	code: str, language: str, forbidden_constructs: list[str] | None = None
) -> tuple[bool, str | None]:
	"""
	Run lightweight static security checks per language before submitting to Judge0.
	Returns (is_safe: bool, error_message: str | None).
	"""
	normalized_lang: str = language.strip().lower()
	custom_set: set[str] = set(forbidden_constructs or [])

	if normalized_lang in {"python", "py", "python3"}:
		try:
			tree: ast.AST = ast.parse(code)
		except SyntaxError as e:
			return False, f"Python Syntax Error: {e.msg} on line {e.lineno}"

		visitor = PythonSecurityVisitor(custom_forbidden=custom_set)
		visitor.visit(tree)

		if visitor.violations:
			return False, visitor.violations[0]

		return True, None

	elif normalized_lang in {"cpp", "c++", "c"}:
		match = CPP_FORBIDDEN_REGEX.search(code)
		if match:
			return False, f"Forbidden construct detected in C++ code: '{match.group(0)}'"

		for construct in custom_set:
			if construct and construct in code:
				return False, f"Forbidden construct '{construct}' detected in C++ code."

		return True, None

	elif normalized_lang in {"java"}:
		match = JAVA_FORBIDDEN_REGEX.search(code)
		if match:
			return False, f"Forbidden construct detected in Java code: '{match.group(0)}'"

		for construct in custom_set:
			if construct and construct in code:
				return False, f"Forbidden construct '{construct}' detected in Java code."

		return True, None

	else:
		return False, f"Unsupported language '{language}' for execution."
