<script setup lang="ts">
import { computed } from 'vue'
import type { ProgressData } from '@/types'
import XpStarBadge from '@/components/common/XpStarBadge.vue'

const props = defineProps<{
	progress: ProgressData | null
	isTodaySolved: boolean
}>()

const currentTier = computed<string>(() => {
	const pts: number = props.progress?.total_points ?? 0
	if (pts >= 1000) return 'Master Coder'
	if (pts >= 500) return 'Gold Apprentice'
	if (pts >= 200) return 'Silver Solver'
	return 'Bronze Explorer'
})

const tierProgressPercent = computed<number>(() => {
	const pts: number = props.progress?.total_points ?? 0
	if (pts >= 1000) return 100
	if (pts >= 500) return Math.min(100, Math.round(((pts - 500) / 500) * 100))
	if (pts >= 200) return Math.min(100, Math.round(((pts - 200) / 300) * 100))
	return Math.min(100, Math.round((pts / 200) * 100))
})

const daysOfWeek = computed<Array<{ day: string; dateStr: string; isPast: boolean; isToday: boolean; isCompleted: boolean }>>(() => {
	const days: Array<{ day: string; dateStr: string; isPast: boolean; isToday: boolean; isCompleted: boolean }> = []
	const now = new Date()
	const dayNames: string[] = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
	const currentDayIndex: number = now.getDay()
	const streak: number = props.progress?.current_streak ?? 0

	// Count working days back from today to determine which cells should be "completed"
	// Only mark days as completed if they fall within the current streak window
	function workingDaysAgo(d: Date): number {
		let count = 0
		const cursor = new Date(now.getFullYear(), now.getMonth(), now.getDate())
		const target = new Date(d.getFullYear(), d.getMonth(), d.getDate())
		while (cursor > target) {
			cursor.setDate(cursor.getDate() - 1)
			if (cursor.getDay() !== 0) count++ // skip Sundays
		}
		return count
	}

	const mondayOffset = currentDayIndex === 0 ? -6 : 1 - currentDayIndex
	for (let i = 0; i < 7; i++) {
		const d = new Date(now)
		d.setDate(now.getDate() + mondayOffset + i)
		const isToday = d.toDateString() === now.toDateString()
		const isPast = d < now && !isToday
		// A past day is completed if it's within the streak window
		// isTodaySolved means today also counts: streak includes today
		let isCompleted = false
		if (isToday) {
			isCompleted = props.isTodaySolved
		} else if (isPast && d.getDay() !== 0) {
			// working days ago from today
			const daysAgo = workingDaysAgo(d)
			// if today is solved, today = day 1 of streak → past days within streak-1 are completed
			// if today is not solved, past days within streak are completed
			const threshold = props.isTodaySolved ? streak - 1 : streak
			isCompleted = streak > 0 && daysAgo <= threshold
		}
		days.push({
			day: dayNames[d.getDay()] || 'Sun',
			dateStr: d.getDate().toString(),
			isPast,
			isToday,
			isCompleted,
		})
	}
	return days
})
</script>

<template>
	<VaCard class="tracker-card">
		<VaCardTitle class="tracker-header">
			<VaIcon name="local_fire_department" color="warning" />
			<span class="tracker-title">Consistency Tracker</span>
		</VaCardTitle>

		<VaCardContent>
			<div class="streak-story">
				<div class="streak-headline">
					<span class="streak-count">{{ progress?.current_streak ?? 0 }}</span>
					<div class="streak-text-group">
						<span class="streak-main-label">Day Active Streak</span>
						<span class="streak-best-label">Personal best: {{ progress?.longest_streak ?? 0 }} days</span>
					</div>
				</div>

				<!-- 7-Day Visual Chain -->
				<VaCard color="backgroundPrimary" class="weekly-chain-card">
					<VaCardContent class="weekly-chain">
						<div
							v-for="(dayItem, idx) in daysOfWeek"
							:key="idx"
							class="day-node"
						>
							<span class="day-name">{{ dayItem.day }}</span>
							<VaAvatar
								size="small"
								:color="dayItem.isCompleted ? 'success' : dayItem.isToday ? 'primary' : 'backgroundElement'"
								:text-color="dayItem.isCompleted || dayItem.isToday ? 'textInverted' : undefined"
							>
								<VaIcon v-if="dayItem.isCompleted" name="check" size="small" />
								<span v-else class="day-num">{{ dayItem.dateStr }}</span>
							</VaAvatar>
						</div>
					</VaCardContent>
				</VaCard>

				<!-- Tier Level Progression -->
				<div class="tier-progress-section">
					<div class="tier-labels">
						<span class="tier-name">{{ currentTier }}</span>
						<XpStarBadge :points="progress?.total_points ?? 0" size="small" />
					</div>
					<VaProgressBar :model-value="tierProgressPercent" :show-percent="false" class="tier-progress-bar" />
					<span class="tier-subtext">Earn points daily by solving assigned questions</span>
				</div>
			</div>
		</VaCardContent>
	</VaCard>
</template>

<style scoped>
.tracker-card {
	border: 1px solid var(--va-background-border);
}

.tracker-header {
	display: flex;
	align-items: center;
	gap: 0.5rem;
}

.tracker-title {
	font-size: 1.05rem;
	font-weight: 700;
	color: var(--va-text-primary);
}

.streak-story {
	display: flex;
	flex-direction: column;
	gap: 1.25rem;
}

.streak-headline {
	display: flex;
	align-items: center;
	gap: 0.85rem;
}

.streak-count {
	font-size: 2.25rem;
	font-weight: 800;
	line-height: 1;
	color: var(--va-warning);
}

.streak-text-group {
	display: flex;
	flex-direction: column;
}

.streak-main-label {
	font-weight: 700;
	font-size: 0.95rem;
	color: var(--va-text-primary);
}

.streak-best-label {
	font-size: 0.75rem;
	color: var(--va-text-secondary);
}

.weekly-chain-card {
	border: 1px solid var(--va-background-border);
}

.weekly-chain {
	display: flex;
	justify-content: space-between;
	padding: 0.75rem 0.5rem;
}

.day-node {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 0.35rem;
}

.day-name {
	font-size: 0.7rem;
	font-weight: 600;
	color: var(--va-text-secondary);
}

.day-num {
	font-size: 0.75rem;
	font-weight: 600;
}

.tier-progress-section {
	display: flex;
	flex-direction: column;
	gap: 0.35rem;
}

.tier-labels {
	display: flex;
	justify-content: space-between;
	font-size: 0.85rem;
	font-weight: 600;
	color: var(--va-text-primary);
}

.tier-progress-bar {
	height: 8px;
}

.tier-subtext {
	font-size: 0.75rem;
	color: var(--va-text-secondary);
}
</style>
