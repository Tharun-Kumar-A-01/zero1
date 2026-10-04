<script setup lang="ts">
import type { StudentRewardBadge } from '@/types'

defineProps<{
	badges: StudentRewardBadge[]
}>()
</script>

<template>
	<VaCard class="badges-card">
		<VaCardTitle class="tracker-header">
			<VaIcon name="verified_user" color="primary" />
			<span class="tracker-title">Earned Milestones</span>
		</VaCardTitle>

		<VaCardContent>
			<VaList v-if="badges && badges.length > 0">
				<VaListItem
					v-for="badge in badges"
					:key="badge.id"
					class="badge-item"
				>
					<VaListItemSection avatar>
						<VaAvatar color="primary" size="small">
							<VaIcon name="military_tech" size="small" />
						</VaAvatar>
					</VaListItemSection>

					<VaListItemSection>
						<VaListItemLabel class="badge-title">
							{{ badge.reward_name }}
						</VaListItemLabel>
						<VaListItemLabel caption>
							Earned {{ new Date(badge.awarded_at).toLocaleDateString() }}
						</VaListItemLabel>
					</VaListItemSection>
				</VaListItem>
			</VaList>

			<div v-else class="no-badges-msg">
				<p>Complete challenges to unlock your first streak milestone badge!</p>
			</div>
		</VaCardContent>
	</VaCard>
</template>

<style scoped>
.badges-card {
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

.badge-item {
	padding: 0.4rem 0;
}

.badge-title {
	font-weight: 600;
	font-size: 0.85rem;
	color: var(--va-text-primary);
}

.no-badges-msg {
	text-align: center;
	padding: 1rem 0.5rem;
	color: var(--va-text-secondary);
	font-size: 0.85rem;
}
</style>
