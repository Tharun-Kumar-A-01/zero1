<script setup lang="ts">
import type { DailyChallengeData } from '@/types'

defineProps<{
	challenge: DailyChallengeData | null
	studentName: string
}>()
</script>

<template>
	<div class="focus-header-bar">
		<div>
			<h1 class="page-title">Daily Practice</h1>
		</div>

		<!-- Flat status strip (no nested cards or shadows) -->
		<div class="status-strip">
			<div class="status-item">
				<VaAvatar
					size="small"
					:color="challenge?.mcq_status === 'correct' ? 'success' : 'backgroundElement'"
					:text-color="challenge?.mcq_status === 'correct' ? 'textInverted' : undefined"
				>
					<VaIcon :name="challenge?.mcq_status === 'correct' ? 'check' : 'help_outline'" size="small" />
				</VaAvatar>
				<span class="status-label">MCQ:</span>
				<VaBadge
					:text="challenge?.mcq_status === 'correct' ? 'Solved (+20 XP)' : challenge?.mcq_status === 'incorrect' ? 'Retry' : 'Pending'"
					:color="challenge?.mcq_status === 'correct' ? 'success' : challenge?.mcq_status === 'incorrect' ? 'danger' : 'secondary'"
				/>
			</div>

			<VaDivider vertical class="strip-divider" />

			<div class="status-item">
				<VaAvatar
					size="small"
					:color="challenge?.coding_status === 'solved' ? 'success' : 'backgroundElement'"
					:text-color="challenge?.coding_status === 'solved' ? 'textInverted' : undefined"
				>
					<VaIcon :name="challenge?.coding_status === 'solved' ? 'check' : 'code'" size="small" />
				</VaAvatar>
				<span class="status-label">Coding:</span>
				<VaBadge
					:text="challenge?.coding_status === 'solved' ? 'Passed (+30 XP)' : challenge?.coding_status === 'attempted_unsolved' ? 'Attempted' : 'Pending'"
					:color="challenge?.coding_status === 'solved' ? 'success' : challenge?.coding_status === 'attempted_unsolved' ? 'warning' : 'secondary'"
				/>
			</div>
		</div>
	</div>
</template>

<style scoped>
.focus-header-bar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	flex-wrap: wrap;
	gap: 1rem;
	margin-bottom: 1.5rem;
	padding-bottom: 1rem;
	border-bottom: 1px solid var(--va-background-border);
}

.page-title {
	font-size: 1.5rem;
	font-weight: 700;
	color: var(--va-text-primary);
	margin: 0;
}

.status-strip {
	display: flex;
	align-items: center;
	gap: 1rem;
	padding: 0.5rem 0.875rem;
	background: var(--va-background-element);
	border: 1px solid var(--va-background-border);
	flex-wrap: wrap;
}

.status-item {
	display: flex;
	align-items: center;
	gap: 0.5rem;
}

.status-label {
	font-size: 0.875rem;
	font-weight: 600;
	color: var(--va-text-primary);
}

.strip-divider {
	height: 1.25rem;
	margin: 0 0.25rem;
}
</style>
