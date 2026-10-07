from __future__ import annotations

import re
from typing import Any


def title_to_function_name(title: str) -> str:
	if not title or not title.strip():
		return "solve"
	words = [w for w in re.sub(r"[^a-zA-Z0-9 ]", " ", title).strip().split() if w]
	if not words:
		return "solve"
	if len(words) == 1:
		return words[0].lower()
	return words[0].lower() + "".join(w.capitalize() for w in words[1:])


def map_python_type(type_str: str) -> str:
	t = (type_str or "").strip().lower()
	if t in ("int", "long", "integer"):
		return "int"
	if t in ("float", "double"):
		return "float"
	if t in ("str", "string", "char"):
		return "str"
	if t in ("bool", "boolean"):
		return "bool"
	if t in ("void", "none"):
		return "None"
	if t.endswith("[][]"):
		inner = map_python_type(t[:-4])
		return f"list[list[{inner}]]"
	if t.endswith("[]"):
		inner = map_python_type(t[:-2])
		return f"list[{inner}]"
	if t.startswith("list[") or t.startswith("dict[") or t.startswith("set["):
		return t
	return "Any"


def map_cpp_type(type_str: str, is_param: bool) -> str:
	t = (type_str or "").strip().lower()
	if t in ("int", "integer"):
		return "int"
	if t in ("long", "long long"):
		return "long long"
	if t == "float":
		return "float"
	if t == "double":
		return "double"
	if t in ("string", "str"):
		return "string"
	if t in ("bool", "boolean"):
		return "bool"
	if t == "char":
		return "char"
	if t == "void":
		return "void"
	if t.endswith("[][]"):
		inner = map_cpp_type(t[:-4], False)
		return f"vector<vector<{inner}>>&" if is_param else f"vector<vector<{inner}>>"
	if t.endswith("[]"):
		inner = map_cpp_type(t[:-2], False)
		return f"vector<{inner}>&" if is_param else f"vector<{inner}>"
	return t or "auto"


def get_cpp_default_return(return_type: str) -> str:
	t = return_type.strip()
	if t == "void":
		return ""
	if t == "bool":
		return "        return false;\n"
	if t in ("int", "long long", "char"):
		return "        return 0;\n"
	if t in ("float", "double"):
		return "        return 0.0;\n"
	if t == "string":
		return '        return "";\n'
	if t.startswith("vector"):
		return "        return {};\n"
	return "        return {};\n"


def map_java_type(type_str: str) -> str:
	t = (type_str or "").strip().lower()
	if t in ("int", "integer"):
		return "int"
	if t == "long":
		return "long"
	if t == "float":
		return "float"
	if t == "double":
		return "double"
	if t in ("string", "str"):
		return "String"
	if t in ("bool", "boolean"):
		return "boolean"
	if t == "char":
		return "char"
	if t == "void":
		return "void"
	if t.endswith("[][]"):
		inner = map_java_type(t[:-4])
		return f"{inner}[][]"
	if t.endswith("[]"):
		inner = map_java_type(t[:-2])
		return f"{inner}[]"
	return "Object"


def get_java_default_return(return_type: str) -> str:
	t = return_type.strip()
	if t == "void":
		return ""
	if t == "boolean":
		return "        return false;\n"
	if t in ("int", "char"):
		return "        return 0;\n"
	if t == "long":
		return "        return 0L;\n"
	if t == "float":
		return "        return 0.0f;\n"
	if t == "double":
		return "        return 0.0;\n"
	if t == "String":
		return '        return "";\n'
	if t.endswith("[][]"):
		base = t.replace("[][]", "")
		return f"        return new {base}[0][0];\n"
	if t.endswith("[]"):
		base = t.replace("[]", "")
		return f"        return new {base}[0];\n"
	return "        return null;\n"


def map_c_type(type_str: str, param_name: str, is_param: bool) -> str:
	t = (type_str or "").strip().lower()
	if t in ("int", "integer"):
		return f"int {param_name}" if is_param else "int"
	if t in ("long", "long long"):
		return f"long long {param_name}" if is_param else "long long"
	if t == "float":
		return f"float {param_name}" if is_param else "float"
	if t == "double":
		return f"double {param_name}" if is_param else "double"
	if t in ("string", "str"):
		return f"char* {param_name}" if is_param else "char*"
	if t in ("bool", "boolean"):
		return f"bool {param_name}" if is_param else "bool"
	if t == "char":
		return f"char {param_name}" if is_param else "char"
	if t == "void":
		return "void"
	if t.endswith("[][]"):
		return f"int** {param_name}, int {param_name}Size, int* {param_name}ColSize" if is_param else "int**"
	if t.endswith("[]"):
		inner = "char*" if t[:-2] == "string" else t[:-2]
		return f"{inner}* {param_name}, int {param_name}Size" if is_param else f"{inner}*"
	return f"int {param_name}" if is_param else "int"


def get_c_default_return(return_type: str) -> str:
	t = return_type.strip()
	if t == "void":
		return ""
	if t == "bool":
		return "    return false;\n"
	if t in ("int", "char", "long long"):
		return "    return 0;\n"
	if t in ("float", "double"):
		return "    return 0.0;\n"
	if "*" in t:
		return "    return NULL;\n"
	return "    return 0;\n"


def resolve_problem_signature(
	title: str = "",
	function_name: str = "",
	parameters: list[dict[str, Any]] | None = None,
	return_type: str = "",
	sample_cases: list[dict[str, Any]] | None = None,
	problem_text: str = "",
) -> tuple[str, list[dict[str, str]], str]:
	clean_title = (title or "").strip()
	clean_problem = (problem_text or "").lower()

	fn = (function_name or "").strip()
	if not fn or fn == "solve":
		fn = title_to_function_name(clean_title) if clean_title else "solve"

	# If explicit non-empty parameters provided
	if parameters:
		valid_params = [
			{"name": str(p.get("name", "")).strip(), "type": str(p.get("type", "int")).strip()}
			for p in parameters
			if str(p.get("name", "")).strip()
		]
		if valid_params:
			return fn, valid_params, (return_type or "").strip() or "int"

	# Dynamic inference
	inferred_return = (return_type or "").strip()
	inferred_params: list[dict[str, str]] = []

	first_sample = sample_cases[0] if sample_cases else {}
	sample_output = str(first_sample.get("expected_output", "")).strip()
	sample_input = str(first_sample.get("input_data", first_sample.get("input", ""))).strip()

	if not inferred_return or inferred_return == "int":
		if sample_output in ("true", "false"):
			inferred_return = "bool"
		elif " " in sample_output and "\n" not in sample_output:
			inferred_return = "int[]"
		elif re.match(r"^-?\d+$", sample_output):
			inferred_return = "int"
		elif re.search(r"[a-zA-Z]", sample_output) and "\n" not in sample_output:
			inferred_return = "string"
		elif "return true" in clean_problem or "return false" in clean_problem or "boolean" in clean_problem:
			inferred_return = "bool"
		elif "return an array" in clean_problem or "return indices" in clean_problem:
			inferred_return = "int[][]" if ("interval" in clean_problem or "matrix" in clean_problem) else "int[]"
		elif "return a string" in clean_problem or "reverse the order of" in clean_problem:
			inferred_return = "string"

	has_target = "target" in clean_problem or len(sample_input.split("\n")) == 3
	mentions_array = any(w in clean_problem for w in ("array", "subarray", "integers"))
	mentions_string = any(w in clean_problem for w in ("string", "palindrome", "substring"))
	mentions_intervals = "interval" in clean_problem or "matrix" in clean_problem

	if mentions_intervals:
		inferred_params.append({"name": "intervals", "type": "int[][]"})
	elif mentions_array and has_target:
		inferred_params.append({"name": "nums", "type": "int[]"})
		inferred_params.append({"name": "target", "type": "int"})
	elif mentions_array:
		inferred_params.append({"name": "nums", "type": "int[]"})
	elif mentions_string:
		inferred_params.append({"name": "s", "type": "string"})
	elif re.match(r"^\d+$", sample_input):
		inferred_params.append({"name": "n", "type": "int"})
	elif re.match(r"^[a-zA-Z0-9: ]+$", sample_input) and "\n" not in sample_input:
		inferred_params.append({"name": "s", "type": "string"})
	else:
		lines = [ln for ln in sample_input.split("\n") if ln.strip()]
		if len(lines) == 3:
			inferred_params.append({"name": "nums", "type": "int[]"})
			inferred_params.append({"name": "target", "type": "int"})
		elif len(lines) == 2 or (len(lines) == 1 and " " in lines[0]):
			inferred_params.append({"name": "nums", "type": "int[]"})
		else:
			inferred_params.append({"name": "nums", "type": "int[]"})

	return fn, inferred_params, inferred_return or "int"


def generate_boilerplate_templates(
	function_name: str,
	parameters: list[dict[str, Any]],
	return_type: str,
) -> dict[str, str]:
	fn = (function_name or "").strip() or "solve"
	ret = (return_type or "").strip() or "int"
	params = [
		{"name": str(p.get("name", "")).strip(), "type": str(p.get("type", "int")).strip()}
		for p in parameters
		if str(p.get("name", "")).strip()
	]

	# 1. Python 3
	py_params = [f"{p['name']}: {map_python_type(p['type'])}" for p in params]
	py_ret = map_python_type(ret)
	py_param_str = (", " + ", ".join(py_params)) if py_params else ""
	python_code = f"""from __future__ import annotations

class Solution:
    def {fn}(self{py_param_str}) -> {py_ret}:
        # Write your solution here
        pass
"""

	# 2. C++ 17
	cpp_params = [f"{map_cpp_type(p['type'], True)} {p['name']}" for p in params]
	cpp_ret = map_cpp_type(ret, False)
	cpp_default_ret = get_cpp_default_return(cpp_ret)
	cpp_params_str = ", ".join(cpp_params)
	cpp_code = f"""#include <iostream>
#include <vector>
#include <string>

using namespace std;

class Solution {{
public:
    {cpp_ret} {fn}({cpp_params_str}) {{
        // Write your solution here
{cpp_default_ret}    }}
}};
"""

	# 3. Java 17
	java_params = [f"{map_java_type(p['type'])} {p['name']}" for p in params]
	java_ret = map_java_type(ret)
	java_default_ret = get_java_default_return(java_ret)
	java_params_str = ", ".join(java_params)
	java_code = f"""import java.util.*;

public class Solution {{
    public {java_ret} {fn}({java_params_str}) {{
        // Write your solution here
{java_default_ret}    }}
}}
"""

	# 4. C
	c_params = [map_c_type(p["type"], p["name"], True) for p in params]
	c_ret = map_c_type(ret, "", False)
	c_default_ret = get_c_default_return(c_ret)
	c_params_str = ", ".join(c_params)
	c_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

{c_ret} {fn}({c_params_str}) {{
    // Write your solution here
{c_default_ret}}}
"""

	return {
		"python": python_code,
		"cpp": cpp_code,
		"java": java_code,
		"c": c_code,
	}
