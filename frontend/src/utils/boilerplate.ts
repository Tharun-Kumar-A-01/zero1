/**
 * Boilerplate code generation utilities for function-based problem creation and solving.
 * Purely dynamic: generates typed signatures and starter templates for any problem,
 * any number of parameters, any data types, and any return type across Python, C++, Java, and C.
 */

export interface ParameterDef {
	name: string
	type: string
}

export interface ProblemSignature {
	functionName: string
	parameters: ParameterDef[]
	returnType: string
}

/**
 * Converts a problem title into a clean camelCase identifier (e.g. "Two Sum" -> "twoSum").
 */
export function titleToFunctionName(title: string): string {
	if (!title || !title.trim()) return 'solve'
	const words = title
		.replace(/[^a-zA-Z0-9 ]/g, ' ')
		.trim()
		.split(/\s+/)
		.filter(Boolean)

	if (words.length === 0 || !words[0]) return 'solve'
	if (words.length === 1) return words[0].toLowerCase()

	return (
		words[0].toLowerCase() +
		words
			.slice(1)
			.map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
			.join('')
	)
}

/**
 * Maps a generic type string (e.g. "int[]", "string", "bool", "int[][]") to a Python 3 type hint.
 */
export function mapPythonType(typeStr: string): string {
	const t = (typeStr || '').trim().toLowerCase()
	if (t === 'int' || t === 'long' || t === 'integer') return 'int'
	if (t === 'float' || t === 'double') return 'float'
	if (t === 'str' || t === 'string' || t === 'char') return 'str'
	if (t === 'bool' || t === 'boolean') return 'bool'
	if (t === 'void' || t === 'none') return 'None'
	if (t.endsWith('[][]')) {
		const inner = mapPythonType(t.slice(0, -4))
		return `list[list[${inner}]]`
	}
	if (t.endsWith('[]')) {
		const inner = mapPythonType(t.slice(0, -2))
		return `list[${inner}]`
	}
	if (t.startsWith('list[') || t.startsWith('dict[') || t.startsWith('set[')) {
		return t
	}
	return 'Any'
}

/**
 * Maps a generic type string to a C++ 17 type.
 */
export function mapCppType(typeStr: string, isParam: boolean): string {
	const t = (typeStr || '').trim().toLowerCase()
	if (t === 'int' || t === 'integer') return 'int'
	if (t === 'long' || t === 'long long') return 'long long'
	if (t === 'float') return 'float'
	if (t === 'double') return 'double'
	if (t === 'string' || t === 'str') return isParam ? 'string' : 'string'
	if (t === 'bool' || t === 'boolean') return 'bool'
	if (t === 'char') return 'char'
	if (t === 'void') return 'void'
	if (t.endsWith('[][]')) {
		const inner = mapCppType(t.slice(0, -4), false)
		return isParam ? `vector<vector<${inner}>>&` : `vector<vector<${inner}>>`
	}
	if (t.endsWith('[]')) {
		const inner = mapCppType(t.slice(0, -2), false)
		return isParam ? `vector<${inner}>&` : `vector<${inner}>`
	}
	return t || 'auto'
}

function getCppDefaultReturn(returnType: string): string {
	const t = returnType.trim()
	if (t === 'void') return ''
	if (t === 'bool') return '        return false;\n'
	if (t === 'int' || t === 'long long' || t === 'char') return '        return 0;\n'
	if (t === 'float' || t === 'double') return '        return 0.0;\n'
	if (t === 'string') return '        return "";\n'
	if (t.startsWith('vector')) return '        return {};\n'
	return '        return {};\n'
}

/**
 * Maps a generic type string to a Java 17 type.
 */
export function mapJavaType(typeStr: string): string {
	const t = (typeStr || '').trim().toLowerCase()
	if (t === 'int' || t === 'integer') return 'int'
	if (t === 'long') return 'long'
	if (t === 'float') return 'float'
	if (t === 'double') return 'double'
	if (t === 'string' || t === 'str') return 'String'
	if (t === 'bool' || t === 'boolean') return 'boolean'
	if (t === 'char') return 'char'
	if (t === 'void') return 'void'
	if (t.endsWith('[][]')) {
		const inner = mapJavaType(t.slice(0, -4))
		return `${inner}[][]`
	}
	if (t.endsWith('[]')) {
		const inner = mapJavaType(t.slice(0, -2))
		return `${inner}[]`
	}
	return 'Object'
}

function getJavaDefaultReturn(returnType: string): string {
	const t = returnType.trim()
	if (t === 'void') return ''
	if (t === 'boolean') return '        return false;\n'
	if (t === 'int' || t === 'char') return '        return 0;\n'
	if (t === 'long') return '        return 0L;\n'
	if (t === 'float') return '        return 0.0f;\n'
	if (t === 'double') return '        return 0.0;\n'
	if (t === 'String') return '        return "";\n'
	if (t.endsWith('[][]')) {
		const base = t.replace('[][]', '')
		return `        return new ${base}[0][0];\n`
	}
	if (t.endsWith('[]')) {
		const base = t.replace('[]', '')
		return `        return new ${base}[0];\n`
	}
	return '        return null;\n'
}

/**
 * Maps a generic type string to a C type with parameter declaration.
 */
export function mapCType(typeStr: string, paramName: string, isParam: boolean): string {
	const t = (typeStr || '').trim().toLowerCase()
	if (t === 'int' || t === 'integer') return isParam ? `int ${paramName}` : 'int'
	if (t === 'long' || t === 'long long') return isParam ? `long long ${paramName}` : 'long long'
	if (t === 'float') return isParam ? `float ${paramName}` : 'float'
	if (t === 'double') return isParam ? `double ${paramName}` : 'double'
	if (t === 'string' || t === 'str') return isParam ? `char* ${paramName}` : 'char*'
	if (t === 'bool' || t === 'boolean') return isParam ? `bool ${paramName}` : 'bool'
	if (t === 'char') return isParam ? `char ${paramName}` : 'char'
	if (t === 'void') return 'void'
	if (t.endsWith('[][]')) {
		return isParam ? `int** ${paramName}, int ${paramName}Size, int* ${paramName}ColSize` : 'int**'
	}
	if (t.endsWith('[]')) {
		const inner = t.slice(0, -2) === 'string' ? 'char*' : t.slice(0, -2)
		return isParam ? `${inner}* ${paramName}, int ${paramName}Size` : `${inner}*`
	}
	return isParam ? `int ${paramName}` : 'int'
}

function getCDefaultReturn(returnType: string): string {
	const t = returnType.trim()
	if (t === 'void') return ''
	if (t === 'bool') return '    return false;\n'
	if (t === 'int' || t === 'char' || t === 'long long') return '    return 0;\n'
	if (t === 'float' || t === 'double') return '    return 0.0;\n'
	if (t.includes('*')) return '    return NULL;\n'
	return '    return 0;\n'
}

/**
 * Dynamically resolves function name, parameters, and return type for ANY problem.
 * If explicit parameters are provided (e.g. from mentor question setup), it uses them.
 * If parameters are empty, it dynamically infers them from the problem's own text,
 * title, and sample test cases.
 */
export function resolveProblemSignature(
	title?: string,
	functionName?: string,
	parameters?: ParameterDef[],
	returnType?: string,
	sampleCases?: Array<{ input_data?: string; expected_output?: string }>,
	problemText?: string
): ProblemSignature {
	const cleanTitle = (title || '').trim()
	const cleanProblem = (problemText || '').toLowerCase()

	// 1. Function name: prioritize explicit function_name, or derive from title
	let fn = (functionName || '').trim()
	if (!fn || fn === 'solve') {
		fn = cleanTitle ? titleToFunctionName(cleanTitle) : 'solve'
	}

	// 2. If explicit non-empty parameters are provided, use them directly
	if (parameters && parameters.length > 0) {
		const validParams = parameters.filter((p) => p.name && p.name.trim())
		if (validParams.length > 0) {
			return {
				functionName: fn,
				parameters: validParams,
				returnType: returnType?.trim() || 'int',
			}
		}
	}

	// 3. Dynamic Inference from Problem Text and Sample Test Cases
	let inferredReturn = (returnType || '').trim()
	const inferredParams: ParameterDef[] = []

	// Inspect sample test cases for output type
	const firstSample = sampleCases && sampleCases.length > 0 ? sampleCases[0] : null
	const sampleOutput = (firstSample?.expected_output || '').trim()
	const sampleInput = (firstSample?.input_data || '').trim()

	if (!inferredReturn || inferredReturn === 'int') {
		if (sampleOutput === 'true' || sampleOutput === 'false') {
			inferredReturn = 'bool'
		} else if (sampleOutput.includes(' ') && !sampleOutput.includes('\n')) {
			inferredReturn = 'int[]'
		} else if (/^-?\d+$/.test(sampleOutput)) {
			inferredReturn = 'int'
		} else if (/[a-zA-Z]/.test(sampleOutput) && !sampleOutput.includes('\n')) {
			inferredReturn = 'string'
		} else if (cleanProblem.includes('return true') || cleanProblem.includes('return false') || cleanProblem.includes('boolean')) {
			inferredReturn = 'bool'
		} else if (cleanProblem.includes('return an array') || cleanProblem.includes('return indices') || cleanProblem.includes('return all overlapping')) {
			inferredReturn = cleanProblem.includes('interval') || cleanProblem.includes('matrix') ? 'int[][]' : 'int[]'
		} else if (cleanProblem.includes('return a string') || cleanProblem.includes('reverse the order of')) {
			inferredReturn = 'string'
		}
	}

	// Dynamic parameter inference from problem text and input format
	const hasTarget = cleanProblem.includes('target') || sampleInput.split('\n').length === 3
	const mentionsArray = cleanProblem.includes('array') || cleanProblem.includes('subarray') || cleanProblem.includes('integers')
	const mentionsString = cleanProblem.includes('string') || cleanProblem.includes('palindrome') || cleanProblem.includes('substring')
	const mentionsIntervals = cleanProblem.includes('interval') || cleanProblem.includes('matrix')

	if (mentionsIntervals) {
		inferredParams.push({ name: 'intervals', type: 'int[][]' })
	} else if (mentionsArray && hasTarget) {
		inferredParams.push({ name: 'nums', type: 'int[]' })
		inferredParams.push({ name: 'target', type: 'int' })
	} else if (mentionsArray) {
		inferredParams.push({ name: 'nums', type: 'int[]' })
	} else if (mentionsString) {
		inferredParams.push({ name: 's', type: 'string' })
	} else if (/^\d+$/.test(sampleInput)) {
		inferredParams.push({ name: 'n', type: 'int' })
	} else if (/^[a-zA-Z0-9: ]+$/.test(sampleInput) && !sampleInput.includes('\n')) {
		inferredParams.push({ name: 's', type: 'string' })
	} else {
		// Fallback based on sample input structure
		const lines = sampleInput.split('\n').filter(Boolean)
		if (lines.length === 3) {
			inferredParams.push({ name: 'nums', type: 'int[]' })
			inferredParams.push({ name: 'target', type: 'int' })
		} else if (lines.length === 2 || (lines.length === 1 && lines[0]?.includes(' '))) {
			inferredParams.push({ name: 'nums', type: 'int[]' })
		} else {
			inferredParams.push({ name: 'nums', type: 'int[]' })
		}
	}

	return {
		functionName: fn,
		parameters: inferredParams,
		returnType: inferredReturn || 'int',
	}
}

/**
 * Generates accurate, idiomatic boilerplate code templates for Python 3, C++ 17, Java 17, and C
 * dynamically based on function name, parameters with types, and return type.
 */
export function generateBoilerplateTemplates(
	functionName: string,
	parameters: ParameterDef[],
	returnType: string
): Record<string, string> {
	const fn = functionName.trim() || 'solve'
	const ret = returnType.trim() || 'int'
	const params = parameters.filter((p) => p.name && p.name.trim())

	// 1. Python 3
	const pyParams = params.map((p) => {
		const mappedType = mapPythonType(p.type)
		return `${p.name}: ${mappedType}`
	})
	const pyRet = mapPythonType(ret)
	const pyParamStr = pyParams.length > 0 ? ', ' + pyParams.join(', ') : ''

	const pythonCode = `from __future__ import annotations

class Solution:
    def ${fn}(self${pyParamStr}) -> ${pyRet}:
        # Write your solution here
        pass
`

	// 2. C++ 17
	const cppParams = params.map((p) => {
		const mappedType = mapCppType(p.type, true)
		return `${mappedType} ${p.name}`
	})
	const cppRet = mapCppType(ret, false)
	const cppDefaultRet = getCppDefaultReturn(cppRet)

	const cppCode = `#include <iostream>
#include <vector>
#include <string>

using namespace std;

class Solution {
public:
    ${cppRet} ${fn}(${cppParams.join(', ')}) {
        // Write your solution here
${cppDefaultRet}    }
};
`

	// 3. Java 17
	const javaParams = params.map((p) => {
		const mappedType = mapJavaType(p.type)
		return `${mappedType} ${p.name}`
	})
	const javaRet = mapJavaType(ret)
	const javaDefaultRet = getJavaDefaultReturn(javaRet)

	const javaCode = `import java.util.*;

public class Solution {
    public ${javaRet} ${fn}(${javaParams.join(', ')}) {
        // Write your solution here
${javaDefaultRet}    }
}
`

	// 4. C
	const cParams = params.map((p) => mapCType(p.type, p.name, true))
	const cRet = mapCType(ret, '', false)
	const cDefaultRet = getCDefaultReturn(cRet)

	const cCode = `#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

${cRet} ${fn}(${cParams.join(', ')}) {
    // Write your solution here
${cDefaultRet}}
`

	return {
		python: pythonCode,
		cpp: cppCode,
		java: javaCode,
		c: cCode,
	}
}

/**
 * Returns dynamic, typed boilerplate templates for any question.
 * Evaluates the question's parameters, return type, and function name dynamically.
 */
export function getProblemStarterTemplates(
	title?: string,
	functionName?: string,
	parameters?: ParameterDef[],
	returnType?: string,
	sampleCases?: Array<{ input_data?: string; expected_output?: string }>,
	existingTemplates?: Record<string, string>,
	problemText?: string
): Record<string, string> {
	// If existingTemplates has custom user-written code or templates that are NOT the dummy static boilerplate, preserve them
	if (existingTemplates && Object.keys(existingTemplates).length > 0) {
		const isStatic = Object.values(existingTemplates).some(
			(t) =>
				t.includes('def solve(self, *args):') ||
				t.includes('int solve() {\n        return 0;\n    }')
		)
		if (!isStatic) {
			return existingTemplates
		}
	}

	const sig = resolveProblemSignature(
		title,
		functionName,
		parameters,
		returnType,
		sampleCases,
		problemText
	)
	return generateBoilerplateTemplates(sig.functionName, sig.parameters, sig.returnType)
}
