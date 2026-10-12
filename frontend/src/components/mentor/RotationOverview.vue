<script setup lang="ts">
import { computed } from 'vue'
import type { QuestionSetData } from '@/types'
import { formatIndianDate } from '@/utils/date'
import PixelProgressBar from '@/components/pixel/PixelProgressBar.vue'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelButton from '@/components/pixel/PixelButton.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'

const props = defineProps<{
	questionSet: QuestionSetData | null
	mcqCount: number
	codingCount: number
	isPublishing: boolean
}>()

const emit = defineEmits<{
	(e: 'publish'): void
}>()

const hasIncompleteCodingQuestions = computed<boolean>(() => {
	if (!props.questionSet?.coding_questions || props.questionSet.coding_questions.length === 0)
		return false
	return props.questionSet.coding_questions.some(
		(q) => (q.sample_test_cases?.length ?? 0) < 3 || (q.hidden_test_cases?.length ?? 0) < 10,
	)
})

const isReadyToPublish = computed<boolean>(
	() => props.mcqCount >= 7 && props.codingCount >= 7 && !hasIncompleteCodingQuestions.value,
)

const readinessPercentage = computed<number>(() => {
	const mcqScore = Math.min(7, props.mcqCount)
	const codingScore = Math.min(7, props.codingCount)
	const baseScore = Math.round(((mcqScore + codingScore) / 14) * 100)
	if (hasIncompleteCodingQuestions.value && baseScore === 100) {
		return 90
	}
	return baseScore
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

		<!-- Readiness Widget -->
		<div class="readiness-strip">
			<div class="meter-info">
				<span class="readiness-label">Readiness:</span>
				<span class="readiness-percent">{{ readinessPercentage }}%</span>
			</div>

			<PixelProgressBar
				:model-value="readinessPercentage"
				color="primary"
				class="readiness-bar"
			/>

			<div class="quota-badges">
				<PixelBadge
					:color="mcqCount >= 7 ? 'success' : 'secondary'"
					:text="`MCQs: ${mcqCount}/7`"
				/>
				<PixelBadge
					:color="codingCount >= 7 ? 'success' : 'secondary'"
					:text="`Coding: ${codingCount}/7`"
				/>
				<PixelBadge
					v-if="hasIncompleteCodingQuestions"
					color="warning"
					text="Test Cases Incomplete"
					title="Every coding problem must have 3 sample and 10 hidden test cases to publish."
				/>
			</div>

			<PixelButton
				v-if="questionSet?.status !== 'published'"
				size="small"
				color="primary"
				:disabled="!isReadyToPublish || !questionSet?.mentor_assignment_id"
				:loading="isPublishing"
				:icon="
					questionSet?.mentor_assignment_id
						? hasIncompleteCodingQuestions
							? 'warning'
							: 'upload'
						: 'clock'
				"
				@click="emit('publish')"
			>
				<template v-if="!questionSet?.mentor_assignment_id">Unassigned Schedule</template>
				<template v-else-if="hasIncompleteCodingQuestions">Fix Incomplete Tests</template>
				<template v-else-if="isReadyToPublish">Publish Question Set</template>
				<template v-else>Incomplete Set (7+7 Req.)</template>
			</PixelButton>

			<PixelBadge v-else color="success" text="LOCKED & PUBLISHED" />
		</div>
	</div>
</template>

<style scoped>
.rotation-header-bar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	flex-wrap: wrap;
	gap: 1.25rem;
	margin-bottom: 1.5rem;
	padding-bottom: 1rem;
	border-bottom: 2px solid var(--pixel-border);
}

.page-title {
	font-family: var(--font-pixel);
	font-size: 1.75rem;
	color: var(--pixel-text);
	margin: 0;
}

.week-subtitle {
	font-size: 0.85rem;
	color: var(--pixel-text-muted);
}

.unassigned-draft-label {
	color: var(--pixel-warning);
}

.readiness-strip {
	display: flex;
	align-items: center;
	gap: 1rem;
	flex-wrap: wrap;
	background-color: var(--pixel-surface);
	border: 2px solid var(--pixel-border);
	box-shadow: 0 3px 0 0 var(--pixel-border-dark);
	border-radius: 4px;
	padding: 8px 14px;
}

.meter-info {
	display: flex;
	align-items: center;
	gap: 6px;
}

.readiness-label {
	font-family: var(--font-pixel);
	font-size: 11px;
	text-transform: uppercase;
	color: var(--pixel-text-dim);
}

.readiness-percent {
	font-family: var(--font-pixel);
	font-size: 13px;
	color: var(--pixel-warning);
}

.readiness-bar {
	width: 120px;
}

.quota-badges {
	display: flex;
	align-items: center;
	gap: 6px;
}
</style>
