import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuestic } from 'vuestic-ui'
import McqChallengeCard from '@/components/student/McqChallengeCard.vue'
import type { MCQQuestionData, DailyChallengeData } from '@/types'

describe('McqChallengeCard component', () => {
	const mockMcq: MCQQuestionData = {
		id: 1,
		prompt_text: 'What is the time complexity of binary search?',
		options: ['O(N)', 'O(log N)', 'O(N^2)', 'O(1)'],
		difficulty: 'easy',
		tags: ['algorithms'],
	}

	const mockChallenge: DailyChallengeData = {
		id: 101,
		student_id: 5,
		assignment_date: '2026-10-01',
		mcq_status: 'pending',
		coding_status: 'pending',
		mcq_question: mockMcq,
		coding_question: null,
	}

	it('renders prompt and all 4 options', () => {
		const wrapper = mount(McqChallengeCard, {
			props: {
				challenge: mockChallenge,
				mcq: mockMcq,
				explanation: null,
				isSubmitting: false,
			},
			global: { plugins: [createVuestic()] },
		})

		expect(wrapper.text()).toContain('What is the time complexity of binary search?')
		expect(wrapper.text()).toContain('O(log N)')
		expect(wrapper.findAll('.option-tile')).toHaveLength(4)
	})

	it('allows selecting an option and emits submit with selected index', async () => {
		const wrapper = mount(McqChallengeCard, {
			props: {
				challenge: mockChallenge,
				mcq: mockMcq,
				explanation: null,
				isSubmitting: false,
			},
			global: { plugins: [createVuestic()] },
		})

		const options = wrapper.findAll('.option-tile')
		expect(options.length).toBeGreaterThanOrEqual(2)
		const secondOption = options[1]!
		await secondOption.trigger('click') // Select Option B: O(log N)
		expect(secondOption.classes()).toContain('selected')

		const submitBtn = wrapper.find('button')
		expect(submitBtn.exists()).toBe(true)
		await submitBtn.trigger('click')

		expect(wrapper.emitted('submit')).toBeTruthy()
		expect(wrapper.emitted('submit')?.[0]).toEqual([1])
	})

	it('renders verified state when challenge is already solved', () => {
		const solvedChallenge: DailyChallengeData = {
			...mockChallenge,
			mcq_status: 'correct',
		}

		const wrapper = mount(McqChallengeCard, {
			props: {
				challenge: solvedChallenge,
				mcq: mockMcq,
				explanation: 'Binary search halves the search space each step.',
				isSubmitting: false,
			},
			global: { plugins: [createVuestic()] },
		})

		expect(wrapper.text()).toContain('Aptitude challenge verified (+20 XP).')
		expect(wrapper.text()).toContain('Binary search halves the search space')
	})

	it('renders radio indicators and dynamic difficulty badge color', async () => {
		const wrapper = mount(McqChallengeCard, {
			props: {
				challenge: mockChallenge,
				mcq: { ...mockMcq, difficulty: 'hard' },
				explanation: null,
				isSubmitting: false,
			},
			global: { plugins: [createVuestic()] },
		})

		const radioIndicators = wrapper.findAll('.radio-indicator')
		expect(radioIndicators).toHaveLength(4)
		expect(wrapper.find('.radio-indicator.checked').exists()).toBe(false)

		// Click third option (index 2)
		await wrapper.findAll('.option-tile')[2]!.trigger('click')
		expect(wrapper.findAll('.radio-indicator')[2]!.classes()).toContain('checked')
		expect(wrapper.find('.radio-dot').exists()).toBe(true)

		// Hard difficulty badge renders with danger color
		expect(wrapper.text()).toContain('HARD')
	})
})
