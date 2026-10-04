import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuestic } from 'vuestic-ui'
import TestcaseConsole from '@/components/student/TestcaseConsole.vue'
import type { SampleTestCase, CodeSubmissionResult } from '@/types'

describe('TestcaseConsole component', () => {
	const sampleCases: SampleTestCase[] = [
		{ id: 1, input_data: '2 3', expected_output: '5', is_sample: true },
		{ id: 2, input_data: '10 20', expected_output: '30', is_sample: true },
	]

	it('renders sample testcases tabs and details', async () => {
		const wrapper = mount(TestcaseConsole, {
			props: {
				sampleTestCases: sampleCases,
				executionResult: null,
				isCollapsed: false,
			},
			global: { plugins: [createVuestic()] },
		})

		expect(wrapper.text()).toContain('Testcase')
		expect(wrapper.text()).toContain('Test Result')
		expect(wrapper.text()).toContain('Case 1')
		expect(wrapper.text()).toContain('Case 2')
		expect(wrapper.text()).toContain('2 3')
		expect(wrapper.text()).toContain('5')

		// Click Case 2
		const caseButtons = wrapper.findAll('.pill-btn')
		await caseButtons[1]!.trigger('click')
		expect(wrapper.text()).toContain('10 20')
		expect(wrapper.text()).toContain('30')
	})

	it('renders execution results on test result tab', async () => {
		const result: CodeSubmissionResult = {
			execution_status: 'passed',
			test_cases_passed: 3,
			test_cases_total: 3,
			runtime_ms: 45,
			memory_kb: 1024,
		}

		const wrapper = mount(TestcaseConsole, {
			props: {
				sampleTestCases: sampleCases,
				executionResult: result,
				isCollapsed: false,
			},
			global: { plugins: [createVuestic()] },
		})

		// Switch to Test Result tab
		const resultTabBtn = wrapper.findAll('.tab-btn')[1]!
		await resultTabBtn.trigger('click')

		expect(wrapper.text()).toContain('Accepted')
		expect(wrapper.text()).toContain('45 ms')
		expect(wrapper.text()).toContain('1024 KB')
		expect(wrapper.text()).toContain('3 / 3')
	})
})
