<script setup lang="ts">
import { computed } from 'vue'
import type { QuestionSetData } from '@/types'
import { formatIndianDate } from '@/utils/date'

const props = defineProps<{
	questionSet: QuestionSetData | null
	mcqCount: number
	codingCount: number
	isPublishing: boolean
}>()

const emit = defineEmits<{
	(e: 'publish'): void
}>()

const isReadyToPublish = computed<boolean>(() => props.mcqCount >= 7 && props.codingCount >= 7)

const readinessPercentage = computed<number>(() => {
	const mcqScore = Math.min(7, props.mcqCount)
	const codingScore = Math.min(7, props.codingCount)
	return Math.round(((mcqScore + codingScore) / 14) * 100)
})
</script>

<template>
	<div class="rotation-header-bar">
		<div>
			<h1 class="page-title">Question Authoring</h1>
			<span v-if="questionSet?.week_start_date" class="week-subtitle">
				Week Starting {{ formatIndianDate(questionSet.week_start_date) }}
			</span>
			<span v-else class="week-subtitle unassigned-draft-label">
				Draft Preparation (No schedule assigned yet)
			</span>
		</div>

		<!-- Flat Readiness Widget (no nested cards or shadows) -->
		<div class="readiness-strip">
			<div class="meter-info">
				<span class="readiness-label">Readiness:</span>
				<span class="readiness-percent">{{ readinessPercentage }}%</span>
			</div>

			<VaProgressBar
				:model-value="readinessPercentage"
				:show-percent="false"
				class="readiness-bar"
			/>

			<div class="quota-badges">
				<VaBadge
					:color="mcqCount >= 7 ? 'success' : 'secondary'"
					:text="`MCQs: ${mcqCount}/7`"
				>
					<template #prepend>
						<VaIcon :name="mcqCount >= 7 ? 'check_circle' : 'radio_button_unchecked'" size="small" />
					</template>
				</VaBadge>
				<VaBadge
					:color="codingCount >= 7 ? 'success' : 'secondary'"
					:text="`Coding: ${codingCount}/7`"
				>
					<template #prepend>
						<VaIcon :name="codingCount >= 7 ? 'check_circle' : 'radio_button_unchecked'" size="small" />
					</template>
				</VaBadge>
			</div>

			<VaButton
				v-if="questionSet?.status !== 'published'"
				size="small"
				:disabled="!isReadyToPublish || !questionSet?.mentor_assignment_id"
				:loading="isPublishing"
				:icon="questionSet?.mentor_assignment_id ? 'send' : 'schedule'"
				@click="emit('publish')"
			>
				{{ !questionSet?.mentor_assignment_id ? 'Awaiting Schedule Assignment' : 'Publish Set' }}
			</VaButton>
			<VaBadge v-else color="success" text="PUBLISHED" />
		</div>
	</div>
</template>

<style scoped>
.rotation-header-bar {
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

.week-subtitle {
	font-size: 0.875rem;
	color: var(--va-secondary);
}

.unassigned-draft-label {
	font-size: 0.8125rem;
	font-weight: 500;
	color: var(--va-info);
}

.readiness-strip {
	display: flex;
	align-items: center;
	gap: 1rem;
	padding: 0.5rem 0.875rem;
	background: var(--va-background-element);
	border: 1px solid var(--va-background-border);
	flex-wrap: wrap;
}

.meter-info {
	display: flex;
	align-items: center;
	gap: 0.25rem;
}

.readiness-label {
	font-size: 0.875rem;
	font-weight: 600;
	color: var(--va-text-primary);
}

.readiness-percent {
	font-size: 0.875rem;
	font-weight: 700;
	color: var(--va-primary);
}

.readiness-bar {
	width: 100px;
}

.quota-badges {
	display: flex;
	gap: 0.5rem;
}
</style>
