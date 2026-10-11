<script setup lang="ts">
import { computed } from 'vue'
import type { LeaderboardEntry } from '@/types'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelCard from '@/components/pixel/PixelCard.vue'
import PixelCardTitle from '@/components/pixel/PixelCardTitle.vue'
import PixelCardContent from '@/components/pixel/PixelCardContent.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'

const props = defineProps<{
	leaderboard: LeaderboardEntry[]
	currentUserId?: number
}>()

// Sort ascending by rank so rank 1 (highest XP) is always at top
const sortedLeaderboard = computed<LeaderboardEntry[]>(() =>
	[...props.leaderboard].sort((a, b) => a.rank - b.rank).slice(0, 5),
)
</script>

<template>
	<PixelCard class="cohort-card">
		<PixelCardTitle class="tracker-header">
			<PixelSprite name="star_gold" :size="18" />
			<span class="tracker-title">Top Peers (Cohort)</span>
		</PixelCardTitle>

		<PixelCardContent>
			<div class="peer-list">
				<div
					v-for="entry in sortedLeaderboard"
					:key="entry.student_id"
					class="peer-item"
					:class="{ 'is-me': entry.student_id === currentUserId }"
				>
					<div class="peer-rank-section">
						<PixelSprite v-if="entry.rank === 1" name="star_gold" :size="20" />
						<PixelSprite v-else-if="entry.rank === 2" name="star_silver" :size="20" />
						<PixelSprite v-else-if="entry.rank === 3" name="star_bronze" :size="20" />
						<span v-else class="peer-rank-num">#{{ entry.rank }}</span>
					</div>

					<div class="peer-info">
						<span class="peer-name">
							{{ entry.name }}
						</span>
						<span class="peer-roll">
							{{ entry.roll_number || 'Student' }}
						</span>
					</div>

					<div class="peer-stats">
						<PixelBadge :text="`${entry.total_points} XP`" color="primary" />
						<span class="peer-streak">
							<PixelSprite name="flame" :size="14" />
							<span>{{ entry.current_streak }}d</span>
						</span>
					</div>
				</div>
			</div>
		</PixelCardContent>
	</PixelCard>
</template>

<style scoped>
.tracker-header {
	display: flex;
	align-items: center;
	gap: 0.6rem;
}

.tracker-title {
	font-family: var(--font-pixel);
	font-size: 13px;
	text-transform: uppercase;
	letter-spacing: 0.04em;
	color: var(--pixel-text);
}

.peer-list {
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.peer-item {
	display: flex;
	align-items: center;
	gap: 12px;
	padding: 8px 10px;
	background-color: var(--pixel-surface-alt);
	border: 1px solid var(--pixel-border);
	border-radius: 3px;
	transition: transform 0.1s;
}

.peer-item.is-me {
	border-color: var(--pixel-btn-primary-bg);
	background-color: rgba(90, 50, 163, 0.18);
}

.peer-rank-section {
	width: 28px;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}

.peer-rank-num {
	font-family: var(--font-pixel);
	font-size: 12px;
	color: var(--pixel-text-dim);
}

.peer-info {
	flex: 1 1 auto;
	display: flex;
	flex-direction: column;
	gap: 2px;
	overflow: hidden;
}

.peer-name {
	font-family: var(--font-body);
	font-weight: 600;
	font-size: 13px;
	color: var(--pixel-text);
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.peer-roll {
	font-size: 11px;
	color: var(--pixel-text-dim);
}

.peer-stats {
	display: flex;
	align-items: center;
	gap: 10px;
	flex-shrink: 0;
}

.peer-streak {
	display: inline-flex;
	align-items: center;
	gap: 4px;
	font-family: var(--font-pixel);
	font-size: 11px;
	color: #fbbf24;
}
</style>
