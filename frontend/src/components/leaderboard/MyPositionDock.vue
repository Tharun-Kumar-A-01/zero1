<script setup lang="ts">
import type { LeaderboardEntry } from '@/types'
import XpStarBadge from '@/components/common/XpStarBadge.vue'

defineProps<{
	entry: LeaderboardEntry
}>()
</script>

<template>
	<VaAffix position="bottom">
		<VaCard square class="my-position-dock" color="backgroundSecondary">
			<VaCardContent class="dock-content">
				<div class="dock-left">
					<VaIcon name="explore" size="large" color="primary" />
					<div class="dock-text">
						<span class="dock-label">Your Current Standing</span>
						<span class="dock-desc">Rank #{{ entry.rank }} in Batch {{ entry.year_batch }}</span>
					</div>
				</div>

				<div class="dock-right">
					<VaBadge color="warning" :text="`${entry.current_streak}d streak`">
						<template #prepend>
							<VaIcon name="local_fire_department" size="small" />
						</template>
					</VaBadge>
					<XpStarBadge :points="entry.total_points" size="small" />
				</div>
			</VaCardContent>
		</VaCard>
	</VaAffix>
</template>

<style scoped>
.my-position-dock {
	border-top: 1px solid var(--va-background-border);
	box-shadow: var(--va-shadow);
	width: 100%;
}

.dock-content {
	max-width: 1200px;
	margin: 0 auto;
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0.85rem 1.5rem;
}

.dock-left {
	display: flex;
	align-items: center;
	gap: 0.75rem;
}

.dock-text {
	display: flex;
	flex-direction: column;
}

.dock-label {
	font-size: 0.75rem;
	font-weight: 600;
	color: var(--va-text-secondary);
}

.dock-desc {
	font-size: 0.95rem;
	font-weight: 700;
	color: var(--va-text-primary);
}

.dock-right {
	display: flex;
	align-items: center;
	gap: 0.75rem;
}
</style>
