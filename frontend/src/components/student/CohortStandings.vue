<script setup lang="ts">
import { computed } from 'vue'
import type { LeaderboardEntry } from '@/types'
import XpStarBadge from '@/components/common/XpStarBadge.vue'

const props = defineProps<{
	leaderboard: LeaderboardEntry[]
	currentUserId?: number
}>()

// Sort ascending by rank so rank 1 (highest XP) is always at top
const sortedLeaderboard = computed<LeaderboardEntry[]>(() =>
	[...props.leaderboard].sort((a, b) => a.rank - b.rank).slice(0, 5)
)
</script>

<template>
	<VaCard class="cohort-card">
		<VaCardTitle class="tracker-header">
			<VaIcon name="people" color="primary" />
			<span class="tracker-title">Top Peers (Batch)</span>
		</VaCardTitle>

		<VaCardContent>
			<VaList class="peer-list">
				<VaListItem
					v-for="entry in sortedLeaderboard"
					:key="entry.student_id"
					class="peer-item"
					:class="{ 'is-me': entry.student_id === currentUserId }"
				>
					<VaListItemSection avatar class="peer-rank-section">
						<VaIcon v-if="entry.rank === 1" name="military_tech" color="warning" size="22px" />
						<VaIcon v-else-if="entry.rank === 2" name="military_tech" color="secondary" size="22px" />
						<VaIcon v-else-if="entry.rank === 3" name="military_tech" color="warning" size="22px" />
						<span v-else class="peer-rank-num">#{{ entry.rank }}</span>
					</VaListItemSection>

					<VaListItemSection>
						<VaListItemLabel class="peer-name">
							{{ entry.name }}
						</VaListItemLabel>
						<VaListItemLabel caption>
							{{ entry.roll_number || 'Student' }}
						</VaListItemLabel>
					</VaListItemSection>

					<VaListItemSection icon class="peer-stats">
						<XpStarBadge :points="entry.total_points" size="small" />
						<span class="peer-streak">
							<VaIcon name="local_fire_department" size="small" class="streak-fire-icon" />
							<span>{{ entry.current_streak }}d</span>
						</span>
					</VaListItemSection>
				</VaListItem>
			</VaList>
		</VaCardContent>
	</VaCard>
</template>

<style scoped>
.cohort-card {
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

.peer-list {
	display: flex;
	flex-direction: column;
	gap: 0.25rem;
}

.peer-item {
	padding: 0.4rem 0.5rem;
	transition: background 0.15s ease;
}

.peer-item.is-me {
	background: var(--va-background-element);
	border: 1px solid var(--va-primary);
}

.peer-rank-section {
	min-width: 32px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.peer-rank-num {
	font-size: 0.85rem;
	font-weight: 700;
	color: var(--va-text-secondary);
}

.peer-name {
	font-weight: 600;
	font-size: 0.88rem;
	color: var(--va-text-primary);
}

.peer-streak {
	display: inline-flex;
	align-items: center;
	gap: 0.15rem;
	font-size: 0.78rem;
	font-weight: 700;
	color: var(--va-text-secondary);
}

.streak-fire-icon {
	color: var(--va-warning);
}

.peer-stats {
	display: flex;
	align-items: center;
	gap: 0.4rem;
}
</style>
