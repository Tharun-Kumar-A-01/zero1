import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuestic } from 'vuestic-ui'
import CodeEditor from '@/components/student/CodeEditor.vue'

describe('CodeEditor component', () => {
	it('renders language selector and textarea', () => {
		const wrapper = mount(CodeEditor, {
			props: {
				modelValue: 'def solve():\n    pass',
				language: 'python',
				starterTemplates: {
					python: 'def solve():\n    pass',
				},
			},
			global: { plugins: [createVuestic()] },
		})

		expect(wrapper.find('textarea').exists()).toBe(true)
		expect(wrapper.text()).toContain('Tab: 4 spaces')
		expect(wrapper.findAll('.line-num')).toHaveLength(2)
	})

	it('emits update:modelValue on typing', async () => {
		const wrapper = mount(CodeEditor, {
			props: {
				modelValue: 'def solve():',
				language: 'python',
			},
			global: { plugins: [createVuestic()] },
		})

		const textarea = wrapper.find('textarea')
		await textarea.setValue('def solve(nums):')
		expect(wrapper.emitted('update:modelValue')).toBeTruthy()
		expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['def solve(nums):'])
	})
})
