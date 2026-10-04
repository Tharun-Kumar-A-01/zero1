<script setup lang="ts">
import { computed } from 'vue'
import type { LeaderboardEntry } from '@/types'

const props = defineProps<{
	entries: LeaderboardEntry[]
}>()

const champion = computed<LeaderboardEntry | null>(() => props.entries[0] || null)
const runnerUp = computed<LeaderboardEntry | null>(() => props.entries[1] || null)
const thirdPlace = computed<LeaderboardEntry | null>(() => props.entries[2] || null)
</script>

<template>
	<section v-if="champion" class="podium-section">
		<!-- 2nd Place -->
		<VaCard v-if="runnerUp" class="podium-card silver-card">
			<VaCardContent class="podium-content">
				<div class="medal-icon silver-medal">
					<VaIcon name="military_tech" size="40px" color="secondary" />
				</div>
				<span class="podium-rank">Rank #2</span>
				<h3 class="podium-name">{{ runnerUp.name }}</h3>
				<span class="podium-roll">{{ runnerUp.roll_number || 'Student' }}</span>
				<div class="podium-stats">
					<VaBadge :text="`${runnerUp.total_points} XP`" color="primary" />
					<VaBadge :text="`${runnerUp.current_streak}d`" color="warning">
						<template #prepend>
							<VaIcon name="local_fire_department" size="small" />
						</template>
					</VaBadge>
				</div>
			</VaCardContent>
		</VaCard>

		<!-- 1st Place (Center / Taller) -->
		<VaCard class="podium-card gold-card">
			<VaCardContent class="podium-content">
				<div class="medal-icon gold-medal">
					<VaIcon name="military_tech" size="48px" color="warning" />
				</div>
				<span class="podium-rank gold-rank">Champion</span>
				<h3 class="podium-name">{{ champion.name }}</h3>
				<span class="podium-roll">{{ champion.roll_number || 'Student' }}</span>
				<div class="podium-stats">
					<VaBadge :text="`${champion.total_points} XP`" color="primary" />
					<VaBadge :text="`${champion.current_streak}d`" color="warning">
						<template #prepend>
							<VaIcon name="local_fire_department" size="small" />
						</template>
					</VaBadge>
				</div>
			</VaCardContent>
		</VaCard>

		<!-- 3rd Place -->
		<VaCard v-if="thirdPlace" class="podium-card bronze-card">
			<VaCardContent class="podium-content">
				<div class="medal-icon bronze-medal">
					<VaIcon name="military_tech" size="36px" color="warning" />
				</div>
				<span class="podium-rank">Rank #3</span>
				<h3 class="podium-name">{{ thirdPlace.name }}</h3>
				<span class="podium-roll">{{ thirdPlace.roll_number || 'Student' }}</span>
				<div class="podium-stats">
					<VaBadge :text="`${thirdPlace.total_points} XP`" color="primary" />
					<VaBadge :text="`${thirdPlace.current_streak}d`" color="warning">
						<template #prepend>
							<VaIcon name="local_fire_department" size="small" />
						</template>
					</VaBadge>
				</div>
			</VaCardContent>
		</VaCard>
	</section>
</template>

<style scoped>
.podium-section {
	display: grid;
	grid-template-columns: 1fr 1.15fr 1fr;
	gap: 1.25rem;
	align-items: end;
	margin-bottom: 2rem;
}

@media (max-width: 768px) {
	.podium-section {
		grid-template-columns: 1fr;
	}
}

.podium-card {
	border: 1px solid var(--va-background-border);
}

.podium-content {
	text-align: center;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 0.35rem;
	padding: 1.5rem 1.25rem;
}

.gold-card {
	border-color: var(--va-warning);
}

.gold-card .podium-content {
	padding-top: 2rem;
	padding-bottom: 2rem;
}

.silver-card {
	border-color: var(--va-secondary);
}

.bronze-card {
	border-color: var(--va-background-border);
}

.medal-icon {
	margin-bottom: 0.35rem;
	display: flex;
	align-items: center;
	justify-content: center;
}

.podium-rank {
	font-size: 0.75rem;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 0.05em;
	color: var(--va-text-secondary);
}

.gold-rank {
	color: var(--va-primary);
}

.podium-name {
	margin: 0.25rem 0 0;
	font-size: 1.15rem;
	font-weight: 700;
	color: var(--va-text-primary);
}

.podium-roll {
	font-size: 0.8rem;
	color: var(--va-text-secondary);
	margin-bottom: 0.5rem;
}

.podium-stats {
	display: flex;
	gap: 0.5rem;
	align-items: center;
}
</style>
