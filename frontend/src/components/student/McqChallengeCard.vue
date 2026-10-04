<script setup lang="ts">
import { ref } from 'vue'
import type { DailyChallengeData, MCQQuestionData } from '@/types'
import { getDifficultyColor } from '@/utils/text'

const props = defineProps<{
	challenge: DailyChallengeData | null
	mcq: MCQQuestionData | null
	explanation: string | null
	isSubmitting: boolean
}>()

const emit = defineEmits<{
	(e: 'submit', optionIndex: number): void
}>()

const selectedOption = ref<number | null>(null)

function handleSelect(index: number): void {
	if (props.challenge?.mcq_status === 'correct') return
	selectedOption.value = index
}

function handleSubmit(): void {
	if (selectedOption.value !== null) {
		emit('submit', selectedOption.value)
	}
}
</script>

<template>
	<VaCard class="challenge-card">
		<VaCardTitle class="card-header-row">
			<div class="question-meta-group">
				<VaBadge text="APTITUDE MCQ" color="primary">
					<template #prepend>
						<VaIcon name="psychology" size="small" />
					</template>
				</VaBadge>
				<VaBadge
					v-if="mcq?.difficulty"
					:text="mcq.difficulty.toUpperCase()"
					:color="getDifficultyColor(mcq.difficulty)"
				/>
			</div>
		</VaCardTitle>

		<VaCardContent>
			<div v-if="mcq" class="mcq-body">
				<p class="question-stem">{{ mcq.prompt_text }}</p>

				<div class="options-container">
					<div
						v-for="(opt, idx) in mcq.options"
						:key="idx"
						class="option-tile"
						:class="{
							selected: selectedOption === idx,
							disabled: challenge?.mcq_status === 'correct'
						}"
						@click="handleSelect(idx)"
					>
						<div class="radio-indicator" :class="{ checked: selectedOption === idx }">
							<div v-if="selectedOption === idx" class="radio-dot" />
						</div>
						<VaBadge
							:text="String.fromCharCode(65 + idx)"
							color="backgroundElement"
						/>
						<span class="option-text">{{ opt }}</span>
					</div>
				</div>

				<VaAlert
					v-if="explanation"
					color="info"
					border="top"
					class="explanation-box"
				>
					<template #icon>
						<VaIcon name="info" />
					</template>
					<strong>Explanation:</strong> {{ explanation }}
				</VaAlert>

				<VaCardActions class="action-footer">
					<VaButton
						v-if="challenge?.mcq_status !== 'correct'"
						:disabled="selectedOption === null"
						:loading="isSubmitting"
						icon="check"
						@click="handleSubmit"
					>
						Submit Answer
					</VaButton>
					<div v-else class="completed-msg">
						<VaIcon name="check_circle" color="success" />
						<span>Aptitude challenge verified (+20 XP).</span>
					</div>
				</VaCardActions>
			</div>

			<div v-else class="empty-state">
				<VaIcon name="inbox" size="48px" color="secondary" class="empty-icon" />
				<p>No MCQ question assigned for today yet.</p>
			</div>
		</VaCardContent>
	</VaCard>
</template>

<style scoped>
.challenge-card {
	border: 1px solid var(--va-background-border);
}

.card-header-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	flex-wrap: wrap;
	gap: 0.75rem;
}

.question-meta-group {
	display: flex;
	align-items: center;
	gap: 0.5rem;
}

.question-stem {
	font-size: 1.05rem;
	line-height: 1.6;
	margin-bottom: 1.25rem;
	color: var(--va-text-primary);
}

.options-container {
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
	margin-bottom: 1.5rem;
}

.option-tile {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	border: 1px solid var(--va-background-border);
	border-radius: 6px;
	padding: 0.75rem 1rem;
	cursor: pointer;
	transition: all 0.15s ease;
	background: var(--va-background-secondary);
}

.option-tile:hover:not(.disabled) {
	border-color: var(--va-primary);
	background: var(--va-background-primary);
}

.option-tile.selected {
	border-color: var(--va-primary);
	background: var(--va-background-element);
}

.option-tile.disabled {
	cursor: default;
}

.radio-indicator {
	width: 18px;
	height: 18px;
	border-radius: 50%;
	border: 2px solid var(--va-background-border);
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
	transition: all 0.2s ease;
}

.radio-indicator.checked {
	border-color: var(--va-primary);
}

.radio-dot {
	width: 10px;
	height: 10px;
	border-radius: 50%;
	background-color: var(--va-primary);
}

.option-text {
	color: var(--va-text-primary);
	font-size: 0.95rem;
}

.explanation-box {
	margin-top: 1rem;
}

.action-footer {
	padding: 1rem 0 0;
	display: flex;
	align-items: center;
	justify-content: flex-end;
}

.completed-msg {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	color: var(--va-success);
	font-weight: 600;
	font-size: 0.9rem;
}

.empty-state {
	text-align: center;
	padding: 3rem 1rem;
	color: var(--va-text-secondary);
}

.empty-icon {
	margin-bottom: 0.5rem;
}
</style>
