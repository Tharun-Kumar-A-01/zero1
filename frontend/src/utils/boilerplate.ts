/**
 * Boilerplate code generation utilities for function-based problem creation.
 */

export interface ParameterDef {
	name: string
	type: string
}

export function generateBoilerplateTemplates(
	functionName: string,
	parameters: ParameterDef[],
	returnType: string
): Record<string, string> {
	const fn = functionName.trim() || 'solve'
	const ret = returnType.trim() || 'int'
	const params = parameters.filter((p) => p.name.trim())

	// 1. Python 3
	const pyParamTypes: Record<string, string> = {
		'int': 'int',
		'float': 'float',
		'string': 'str',
		'str': 'str',
		'bool': 'bool',
		'boolean': 'bool',
		'int[]': 'list[int]',
		'string[]': 'list[str]',
		'int[][]': 'list[list[int]]',
	}
	const pyParams = params.map((p) => {
		const mappedType = pyParamTypes[p.type.toLowerCase()] || 'Any'
		return `${p.name}: ${mappedType}`
	})
	const pyRet = pyParamTypes[ret.toLowerCase()] || (ret === 'void' ? 'None' : 'Any')

	const pythonCode = `class Solution:
    def ${fn}(self, ${pyParams.join(', ')}) -> ${pyRet}:
        # Write your solution here
        pass
`

	// 2. C++ 17
	const cppTypes: Record<string, string> = {
		'int': 'int',
		'float': 'double',
		'double': 'double',
		'string': 'string',
		'str': 'string',
		'bool': 'bool',
		'boolean': 'bool',
		'void': 'void',
		'int[]': 'vector<int>&',
		'string[]': 'vector<string>&',
		'int[][]': 'vector<vector<int>>&',
	}
	const cppRetTypes: Record<string, string> = {
		'int': 'int',
		'float': 'double',
		'double': 'double',
		'string': 'string',
		'str': 'string',
		'bool': 'bool',
		'boolean': 'bool',
		'void': 'void',
		'int[]': 'vector<int>',
		'string[]': 'vector<string>',
		'int[][]': 'vector<vector<int>>',
	}
	const cppParams = params.map((p) => {
		const mappedType = cppTypes[p.type.toLowerCase()] || 'auto'
		return `${mappedType} ${p.name}`
	})
	const cppRet = cppRetTypes[ret.toLowerCase()] || 'int'
	const cppDefaultRet = cppRet === 'void' ? '' : cppRet.startsWith('vector') ? '        return {};\n' : cppRet === 'bool' ? '        return false;\n' : cppRet === 'string' ? '        return "";\n' : '        return 0;\n'

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
	const javaTypes: Record<string, string> = {
		'int': 'int',
		'float': 'double',
		'double': 'double',
		'string': 'String',
		'str': 'String',
		'bool': 'boolean',
		'boolean': 'boolean',
		'void': 'void',
		'int[]': 'int[]',
		'string[]': 'String[]',
		'int[][]': 'int[][]',
	}
	const javaParams = params.map((p) => {
		const mappedType = javaTypes[p.type.toLowerCase()] || 'Object'
		return `${mappedType} ${p.name}`
	})
	const javaRet = javaTypes[ret.toLowerCase()] || 'int'
	const javaDefaultRet = javaRet === 'void' ? '' : javaRet.endsWith('[]') ? `        return new ${javaRet.replace('[]', '')}[0];\n` : javaRet === 'boolean' ? '        return false;\n' : javaRet === 'String' ? '        return "";\n' : '        return 0;\n'

	const javaCode = `import java.util.*;

public class Solution {
    public ${javaRet} ${fn}(${javaParams.join(', ')}) {
        // Write your solution here
${javaDefaultRet}    }
}
`

	// 4. C
	const cTypes: Record<string, string> = {
		'int': 'int',
		'float': 'double',
		'double': 'double',
		'string': 'char*',
		'str': 'char*',
		'bool': 'bool',
		'boolean': 'bool',
		'void': 'void',
		'int[]': 'int*',
		'string[]': 'char**',
	}
	const cParams = params.map((p) => {
		const mappedType = cTypes[p.type.toLowerCase()] || 'int'
		return `${mappedType} ${p.name}`
	})
	const cRet = cTypes[ret.toLowerCase()] || 'int'
	const cDefaultRet = cRet === 'void' ? '' : cRet.includes('*') ? '    return NULL;\n' : cRet === 'bool' ? '    return false;\n' : '    return 0;\n'

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
