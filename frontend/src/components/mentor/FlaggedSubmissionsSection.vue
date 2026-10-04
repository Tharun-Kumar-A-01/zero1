<script setup lang="ts">
import type { FlaggedSubmission } from '@/types'

defineProps<{
	flaggedSubmissions: FlaggedSubmission[]
	isSubmitting: boolean
}>()

const emit = defineEmits<{
	(e: 'resolve', payload: { submissionId: number; resolution: 'dismiss' | 'action' }): void
}>()
</script>

<template>
	<div class="pool-container">
		<div class="pool-header">
			<div>
				<h2 class="section-title">Flagged Submissions Queue</h2>
				<p class="section-desc">Review AST-detected security policy breaches and blocked system calls.</p>
			</div>
		</div>

		<div v-if="flaggedSubmissions.length > 0" class="cards-list">
			<VaCard
				v-for="sub in flaggedSubmissions"
				:key="sub.id"
				class="item-card flagged-card"
			>
				<VaCardContent>
					<div class="card-inner">
						<div class="card-meta">
							<VaBadge color="danger" text="SECURITY VIOLATION" />
							<span class="meta-tag"><VaIcon name="person" size="small" /> Assignment #{{ sub.daily_assignment_id }}</span>
							<span class="meta-tag"><VaIcon name="calendar_today" size="small" /> {{ new Date(sub.submitted_at || sub.created_at || Date.now()).toLocaleString() }}</span>
						</div>

						<VaCard color="backgroundElement" class="code-snippet-card">
							<VaCardContent class="snippet-content">
								<pre class="snippet-code">{{ sub.source_code }}</pre>
							</VaCardContent>
						</VaCard>

						<VaCardActions class="review-actions">
							<VaButton
								color="danger"
								size="small"
								icon="delete"
								@click="emit('resolve', { submissionId: sub.id, resolution: 'action' })"
							>
								Strike Student
							</VaButton>
							<VaButton
								size="small"
								color="success"
								icon="check"
								@click="emit('resolve', { submissionId: sub.id, resolution: 'dismiss' })"
							>
								Dismiss Flag
							</VaButton>
						</VaCardActions>
					</div>
				</VaCardContent>
			</VaCard>
		</div>

		<VaCard v-else class="empty-pool-card">
			<VaCardContent class="empty-content">
				<VaIcon name="verified_user" size="48px" color="success" class="empty-pool-icon" />
				<h3>No Flagged Submissions</h3>
				<p>All student code submissions conform to AST sandbox policies.</p>
			</VaCardContent>
		</VaCard>
	</div>
</template>

<style scoped>
.pool-container {
	display: flex;
	flex-direction: column;
	gap: 1.25rem;
}

.pool-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.section-title {
	margin: 0;
	font-size: 1.2rem;
	font-weight: 700;
	color: var(--va-text-primary);
}

.section-desc {
	margin: 0.25rem 0 0;
	font-size: 0.85rem;
	color: var(--va-text-secondary);
}

.cards-list {
	display: flex;
	flex-direction: column;
	gap: 1rem;
}

.item-card {
	border: 1px solid var(--va-background-border);
}

.card-inner {
	display: flex;
	flex-direction: column;
	gap: 0.75rem;
}

.card-meta {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	flex-wrap: wrap;
}

.meta-tag {
	font-size: 0.75rem;
	color: var(--va-text-secondary);
	display: inline-flex;
	align-items: center;
	gap: 0.25rem;
}

.flagged-card {
	border-left: 4px solid var(--va-danger);
}

.code-snippet-card {
	border: 1px solid var(--va-background-border);
}

.snippet-content {
	padding: 0.75rem;
}

.snippet-code {
	color: var(--va-text-primary);
	margin: 0;
	font-family: monospace;
	font-size: 0.85rem;
	max-height: 200px;
	overflow-y: auto;
}

.review-actions {
	padding: 0;
	display: flex;
	gap: 0.5rem;
	justify-content: flex-end;
}

.empty-pool-card {
	border: 2px dashed var(--va-background-border);
}

.empty-content {
	padding: 3rem 2rem;
	text-align: center;
	color: var(--va-text-secondary);
}

.empty-pool-icon {
	margin-bottom: 0.75rem;
}
</style>
