import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuestic } from 'vuestic-ui'
import ConsistencyTracker from '@/components/student/ConsistencyTracker.vue'
import type { ProgressData } from '@/types'

describe('ConsistencyTracker component', () => {
	it('renders active streak count, longest streak, and tier level', () => {
		const mockProgress: ProgressData = {
			current_streak: 6,
			longest_streak: 12,
			total_points: 250,
			badges: [],
		}

		const wrapper = mount(ConsistencyTracker, {
			props: {
				progress: mockProgress,
				isTodaySolved: false,
			},
			global: { plugins: [createVuestic()] },
		})

		expect(wrapper.text()).toContain('6')
		expect(wrapper.text()).toContain('Personal best: 12 days')
		expect(wrapper.text()).toContain('Silver Solver') // 250 pts is Silver Solver tier
		expect(wrapper.text()).toContain('250XP')
		expect(wrapper.findAll('.day-node')).toHaveLength(7)
	})

	it('computes Master Coder tier when points reach 1000', () => {
		const masterProgress: ProgressData = {
			current_streak: 30,
			longest_streak: 30,
			total_points: 1200,
			badges: [],
		}

		const wrapper = mount(ConsistencyTracker, {
			props: {
				progress: masterProgress,
				isTodaySolved: true,
			},
			global: { plugins: [createVuestic()] },
		})

		expect(wrapper.text()).toContain('Master Coder')
		expect(wrapper.text()).toContain('1200XP')
	})
})
