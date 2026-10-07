import { describe, it, expect } from 'vitest'
import {
	generateBoilerplateTemplates,
	resolveProblemSignature,
	titleToFunctionName,
	mapPythonType,
	mapCppType,
	mapJavaType,
	mapCType,
} from '../boilerplate'

describe('boilerplate generation (dynamic and generic)', () => {
	it('converts titles to camelCase function names', () => {
		expect(titleToFunctionName('Two Sum')).toBe('twoSum')
		expect(titleToFunctionName('Longest Substring Without Repeating Characters')).toBe(
			'longestSubstringWithoutRepeatingCharacters'
		)
		expect(titleToFunctionName('Find Kth Largest Element in Array')).toBe(
			'findKthLargestElementInArray'
		)
		expect(titleToFunctionName('')).toBe('solve')
	})

	it('maps types correctly across languages', () => {
		// Python
		expect(mapPythonType('int[]')).toBe('list[int]')
		expect(mapPythonType('string')).toBe('str')
		expect(mapPythonType('int[][]')).toBe('list[list[int]]')
		expect(mapPythonType('bool')).toBe('bool')

		// C++
		expect(mapCppType('int[]', true)).toBe('vector<int>&')
		expect(mapCppType('int[]', false)).toBe('vector<int>')
		expect(mapCppType('string', true)).toBe('string')
		expect(mapCppType('int[][]', true)).toBe('vector<vector<int>>&')

		// Java
		expect(mapJavaType('int[]')).toBe('int[]')
		expect(mapJavaType('string')).toBe('String')
		expect(mapJavaType('int[][]')).toBe('int[][]')
		expect(mapJavaType('bool')).toBe('boolean')

		// C
		expect(mapCType('int[]', 'nums', true)).toBe('int* nums, int numsSize')
		expect(mapCType('string', 's', true)).toBe('char* s')
		expect(mapCType('int', 'val', true)).toBe('int val')
	})

	it('generates accurate templates for multi-parameter and custom problem', () => {
		const templates = generateBoilerplateTemplates(
			'customSearch',
			[
				{ name: 'grid', type: 'int[][]' },
				{ name: 'query', type: 'string' },
				{ name: 'threshold', type: 'float' },
			],
			'bool'
		)

		// Python
		expect(templates.python).toContain('class Solution:')
		expect(templates.python).toContain(
			'def customSearch(self, grid: list[list[int]], query: str, threshold: float) -> bool:'
		)

		// C++
		expect(templates.cpp).toContain('class Solution {')
		expect(templates.cpp).toContain(
			'bool customSearch(vector<vector<int>>& grid, string query, float threshold)'
		)
		expect(templates.cpp).toContain('return false;')

		// Java
		expect(templates.java).toContain('public class Solution {')
		expect(templates.java).toContain(
			'public boolean customSearch(int[][] grid, String query, float threshold)'
		)
		expect(templates.java).toContain('return false;')

		// C
		expect(templates.c).toContain('bool customSearch(')
		expect(templates.c).toContain('int** grid, int gridSize, int* gridColSize')
		expect(templates.c).toContain('char* query')
		expect(templates.c).toContain('float threshold')
	})

	it('dynamically infers parameters from problem description and testcases when empty', () => {
		const sig = resolveProblemSignature(
			'Check Substring Presence',
			'solve',
			[],
			'',
			[{ input_data: 'hello world', expected_output: 'true' }],
			'Given a string s, return true if condition holds.'
		)

		expect(sig.functionName).toBe('checkSubstringPresence')
		expect(sig.parameters).toEqual([{ name: 's', type: 'string' }])
		expect(sig.returnType).toBe('bool')
	})
})
