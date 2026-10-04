<script setup lang="ts">
import type { LeaderboardEntry } from '@/types'

defineProps<{
	entries: LeaderboardEntry[]
	currentUserId?: number
}>()

const columns = [
	{ key: 'rank', label: 'Rank', sortable: true },
	{ key: 'name', label: 'Student', sortable: true },
	{ key: 'roll_number', label: 'Roll Number' },
	{ key: 'year_batch', label: 'Batch' },
	{ key: 'current_streak', label: 'Daily Streak', sortable: true },
	{ key: 'total_points', label: 'Total Score', sortable: true },
]
</script>

<template>
	<div class="rankings-container">
		<VaCard v-if="entries.length > 0">
			<VaCardContent>
				<VaDataTable
					:items="entries"
					:columns="columns"
					striped
					hoverable
				>
					<template #cell(rank)="{ value }">
						<div class="rank-cell">
							<VaIcon v-if="Number(value) === 1" name="military_tech" color="warning" size="22px" />
							<VaIcon v-else-if="Number(value) === 2" name="military_tech" color="secondary" size="22px" />
							<VaIcon v-else-if="Number(value) === 3" name="military_tech" color="warning" size="22px" />
							<span v-else class="rank-number">#{{ value }}</span>
						</div>
					</template>

					<template #cell(name)="{ rowData }">
						<div class="student-cell">
							<VaAvatar size="small" color="primary">
								{{ (rowData as LeaderboardEntry).name.split(' ').map((n) => n[0]).join('').substring(0, 2).toUpperCase() }}
							</VaAvatar>
							<div class="student-name-group">
								<span class="student-fullname">{{ (rowData as LeaderboardEntry).name }}</span>
								<VaBadge
									v-if="(rowData as LeaderboardEntry).student_id === currentUserId"
									text="YOU"
									color="primary"
								/>
							</div>
						</div>
					</template>

					<template #cell(roll_number)="{ value }">
						<span>{{ value || '—' }}</span>
					</template>

					<template #cell(year_batch)="{ value }">
						<span>{{ value ? `Batch ${value}` : '—' }}</span>
					</template>

					<template #cell(current_streak)="{ value }">
						<VaBadge
							color="warning"
							:text="`${value}d`"
						>
							<template #prepend>
								<VaIcon name="local_fire_department" size="small" />
							</template>
						</VaBadge>
					</template>

					<template #cell(total_points)="{ value }">
						<span class="points-val">{{ value }} XP</span>
					</template>
				</VaDataTable>
			</VaCardContent>
		</VaCard>

		<VaCard v-else class="empty-leaderboard-card">
			<VaCardContent class="empty-state">
				<VaIcon name="emoji_events" size="48px" color="secondary" class="empty-icon" />
				<h3>No rankings recorded yet</h3>
				<p>Be the first student in this batch to solve today's challenge and top the leaderboard!</p>
			</VaCardContent>
		</VaCard>
	</div>
</template>

<style scoped>
.rankings-container {
	display: flex;
	flex-direction: column;
	gap: 1rem;
}

.rank-cell {
	display: flex;
	align-items: center;
	font-weight: 700;
}

.rank-number {
	color: var(--va-text-secondary);
}

.student-cell {
	display: flex;
	align-items: center;
	gap: 0.75rem;
}

.student-name-group {
	display: flex;
	align-items: center;
	gap: 0.5rem;
}

.student-fullname {
	font-weight: 600;
	color: var(--va-text-primary);
}

.points-val {
	font-weight: 700;
	color: var(--va-primary);
}

.empty-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	text-align: center;
	padding: 3rem 2rem;
	color: var(--va-text-secondary);
}

.empty-icon {
	margin-bottom: 0.75rem;
}
</style>
