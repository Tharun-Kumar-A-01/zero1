from __future__ import annotations

from app.services.code_analyzer import analyze_student_code


def test_valid_python_passes() -> None:
	code: str = """
def two_sum(nums, target):
	seen = {}
	for i, num in enumerate(nums):
		diff = target - num
		if diff in seen:
			return [seen[diff], i]
		seen[num] = i
	return []
"""
	is_safe, error = analyze_student_code(code, "python")
	assert is_safe is True
	assert error is None


def test_python_threading_blocked() -> None:
	code: str = "import threading\nt = threading.Thread(target=lambda: None)"
	is_safe, error = analyze_student_code(code, "python")
	assert is_safe is False
	assert error is not None
	assert "threading" in error


def test_python_os_subprocess_blocked() -> None:
	code: str = "from subprocess import Popen\nPopen(['ls'])"
	is_safe, error = analyze_student_code(code, "python")
	assert is_safe is False
	assert "subprocess" in str(error)


def test_python_eval_open_calls_blocked() -> None:
	code_eval: str = "result = eval('2 + 2')"
	is_safe, error = analyze_student_code(code_eval, "python")
	assert is_safe is False
	assert "eval" in str(error)

	code_open: str = "with open('/etc/passwd') as f:\n\tpass"
	is_safe, error = analyze_student_code(code_open, "python")
	assert is_safe is False
	assert "open" in str(error)


def test_python_custom_forbidden_construct() -> None:
	code: str = "import math\nprint(math.sqrt(16))"
	is_safe, error = analyze_student_code(code, "python", forbidden_constructs=["math"])
	assert is_safe is False
	assert "Forbidden construct 'math'" in str(error)


def test_valid_cpp_passes() -> None:
	code: str = """
#include <iostream>
#include <vector>
using namespace std;
int main() {
	int a, b;
	if (cin >> a >> b) cout << a + b << endl;
	return 0;
}
"""
	is_safe, error = analyze_student_code(code, "cpp")
	assert is_safe is True
	assert error is None


def test_cpp_threading_or_fork_blocked() -> None:
	code_thread: str = "#include <iostream>\n#include <thread>\nint main() {}"
	is_safe, error = analyze_student_code(code_thread, "cpp")
	assert is_safe is False

	code_fork: str = "#include <iostream>\nint main() { fork(); return 0; }"
	is_safe, error = analyze_student_code(code_fork, "cpp")
	assert is_safe is False


def test_java_threading_blocked() -> None:
	code: str = "public class Solution { void run() { java.lang.Thread t = new Thread(); } }"
	is_safe, error = analyze_student_code(code, "java")
	assert is_safe is False
	assert "Forbidden construct" in str(error)
