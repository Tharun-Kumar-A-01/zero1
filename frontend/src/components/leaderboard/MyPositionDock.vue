<script setup lang="ts">
import type { LeaderboardEntry } from '@/types'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'
import PixelAvatar from '@/components/pixel/PixelAvatar.vue'

defineProps<{
	entry: LeaderboardEntry
}>()
</script>

<template>
	<div class="my-position-dock">
		<div class="dock-content">
			<div class="dock-left">
				<PixelAvatar size="small" color="primary" :avatar="entry.avatar">
					{{ entry.name.charAt(0).toUpperCase() }}
				</PixelAvatar>
				<div class="dock-text">
					<span class="dock-label">Your Current Standing</span>
					<span class="dock-desc"
						>Rank #{{ entry.rank }} in Batch {{ entry.year_batch }}</span
					>
				</div>
			</div>

			<div class="dock-right">
				<div class="streak-pill">
					<PixelSprite name="flame" :size="14" />
					<span>{{ entry.current_streak }}d streak</span>
				</div>
				<PixelBadge :text="`${entry.total_points} XP`" color="primary" />
			</div>
		</div>
	</div>
</template>

<style scoped>
.my-position-dock {
	position: fixed;
	bottom: 0;
	left: 250px;
	right: 0;
	background-color: var(--pixel-surface);
	border-top: 3px solid var(--pixel-border);
	box-shadow:
		0 -4px 0 0 var(--pixel-border-dark),
		0 -8px 24px rgba(0, 0, 0, 0.5);
	z-index: 90;
}

@media (max-width: 768px) {
	.my-position-dock {
		left: 0;
		bottom: 56px !important;
	}
}

@media (min-width: 769px) and (max-width: 1024px) {
	.my-position-dock {
		left: 72px;
	}
}

.dock-content {
	max-width: 1200px;
	margin: 0 auto;
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0.75rem 1.5rem;
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
	font-family: var(--font-pixel);
	font-size: 11px;
	text-transform: uppercase;
	color: var(--pixel-text-dim);
}

.dock-desc {
	font-family: var(--font-pixel);
	font-size: 13px;
	color: var(--pixel-text);
}

.dock-right {
	display: flex;
	align-items: center;
	gap: 1rem;
}

.streak-pill {
	display: inline-flex;
	align-items: center;
	gap: 4px;
	background-color: #2b1704;
	border: 1px solid #7e4507;
	padding: 3px 8px;
	border-radius: 3px;
	font-family: var(--font-pixel);
	font-size: 11px;
	color: #fbbf24;
}
</style>
