<script setup lang="ts">
import { ref, computed } from 'vue'
import type { DailyChallengeData, MCQQuestionData } from '@/types'
import { getDifficultyColor } from '@/utils/text'
import PixelCard from '@/components/pixel/PixelCard.vue'
import PixelCardTitle from '@/components/pixel/PixelCardTitle.vue'
import PixelCardContent from '@/components/pixel/PixelCardContent.vue'
import PixelCardActions from '@/components/pixel/PixelCardActions.vue'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelButton from '@/components/pixel/PixelButton.vue'
import PixelAlert from '@/components/pixel/PixelAlert.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'

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

const isAttended = computed<boolean>(() => {
	return !!props.challenge?.mcq_status && props.challenge.mcq_status !== 'pending'
})

const markedOptionIndex = computed<number | null>(() => {
	if (selectedOption.value !== null) return selectedOption.value
	if (
		props.challenge?.mcq_selected_option_index !== undefined &&
		props.challenge.mcq_selected_option_index !== null
	) {
		return props.challenge.mcq_selected_option_index
	}
	return null
})

const correctOptionIndex = computed<number | null>(() => {
	if (
		props.challenge?.mcq_correct_option_index !== undefined &&
		props.challenge.mcq_correct_option_index !== null
	) {
		return props.challenge.mcq_correct_option_index
	}
	if (props.mcq?.correct_option_index !== undefined && props.mcq.correct_option_index !== null) {
		return props.mcq.correct_option_index
	}
	return null
})

function handleSelect(index: number): void {
	if (isAttended.value) return
	selectedOption.value = index
}

function handleSubmit(): void {
	if (selectedOption.value !== null) {
		emit('submit', selectedOption.value)
	}
}
</script>

<template>
	<PixelCard class="challenge-card">
		<PixelCardTitle class="card-header-row">
			<div class="question-meta-group">
				<span class="card-type-title">APTITUDE MCQ</span>
				<PixelBadge
					v-if="mcq?.difficulty"
					:text="mcq.difficulty.toUpperCase()"
					:color="getDifficultyColor(mcq.difficulty)"
				/>
				<PixelBadge text="+20 XP" color="primary" />
			</div>
		</PixelCardTitle>

		<PixelCardContent>
			<div v-if="mcq" class="mcq-body">
				<p class="question-stem">{{ mcq.prompt_text }}</p>

				<div class="options-container">
					<div
						v-for="(opt, idx) in mcq.options"
						:key="idx"
						class="option-tile"
						:class="{
							selected: !isAttended && selectedOption === idx,
							disabled: isAttended,
							'is-correct-option': isAttended && correctOptionIndex === idx,
							'is-wrong-marked':
								isAttended &&
								markedOptionIndex === idx &&
								correctOptionIndex !== idx,
						}"
						@click="handleSelect(idx)"
					>
						<!-- Radio Indicator (Active Mode) -->
						<div
							v-if="!isAttended"
							class="radio-indicator"
							:class="{ checked: selectedOption === idx }"
						>
							<div v-if="selectedOption === idx" class="radio-dot" />
						</div>

						<!-- Attended Status Icon -->
						<div
							v-else-if="correctOptionIndex === idx"
							class="result-indicator correct-icon"
						>
							<PixelIcon name="check" :size="14" color="#10b981" />
						</div>
						<div
							v-else-if="markedOptionIndex === idx"
							class="result-indicator wrong-icon"
						>
							<PixelIcon name="cross" :size="14" color="#ef4444" />
						</div>
						<div v-else class="result-indicator neutral-dot">
							<span class="neutral-dash">—</span>
						</div>

						<span class="option-prefix">{{ String.fromCharCode(65 + idx) }}.</span>
						<span class="option-text">{{ opt }}</span>

						<!-- Attended Choice Badges -->
						<div v-if="isAttended" class="option-badges-wrap">
							<PixelBadge
								v-if="correctOptionIndex === idx && markedOptionIndex === idx"
								text="YOUR ANSWER ✓"
								color="success"
							/>
							<PixelBadge
								v-else-if="correctOptionIndex === idx"
								text="CORRECT ANSWER"
								color="success"
							/>
							<PixelBadge
								v-else-if="markedOptionIndex === idx"
								text="YOUR ANSWER ✗"
								color="danger"
							/>
						</div>
					</div>
				</div>

				<PixelAlert v-if="explanation" color="info" class="explanation-box">
					<strong>Explanation:</strong> {{ explanation }}
				</PixelAlert>

				<PixelCardActions class="action-footer">
					<PixelButton
						v-if="!isAttended"
						color="primary"
						:disabled="selectedOption === null"
						:loading="isSubmitting"
						icon="check"
						@click="handleSubmit"
					>
						Submit Answer
					</PixelButton>
					<div
						v-else-if="challenge?.mcq_status === 'correct'"
						class="completed-msg success-msg"
					>
						<PixelIcon name="check" :size="16" color="#34d399" />
						<span>Aptitude challenge verified (+20 XP).</span>
					</div>
					<div v-else class="completed-msg incorrect-msg">
						<PixelIcon name="cross" :size="16" color="#ef4444" />
						<span
							>Aptitude challenge completed. Marked and correct options are shown
							above.</span
						>
					</div>
				</PixelCardActions>
			</div>

			<div v-else class="empty-state">
				<PixelSprite name="scroll" :size="36" class="empty-icon" />
				<p>No MCQ question assigned for today yet.</p>
			</div>
		</PixelCardContent>
	</PixelCard>
</template>

<style scoped>
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

.card-type-title {
	font-family: var(--font-pixel);
	font-size: 11px;
	text-transform: uppercase;
	letter-spacing: 0.04em;
	color: var(--pixel-text);
	line-height: 1;
}

.mcq-body {
	display: flex;
	flex-direction: column;
	gap: 1.25rem;
}

.question-stem {
	font-size: 1.05rem;
	line-height: 1.6;
	color: var(--pixel-text);
	margin: 0;
}

.options-container {
	display: flex;
	flex-direction: column;
	gap: 0.65rem;
}

.option-tile {
	display: flex;
	align-items: center;
	gap: 0.85rem;
	padding: 10px 14px;
	background-color: var(--pixel-surface-alt);
	border: 2px solid var(--pixel-border);
	box-shadow: 0 3px 0 0 rgba(0, 0, 0, 0.3);
	border-radius: 3px;
	cursor: pointer;
	user-select: none;
	transition: all 0.08s ease;
}

.option-tile:hover:not(.disabled) {
	background-color: var(--pixel-surface-raised);
	border-color: var(--pixel-border-bright);
}

.option-tile.selected {
	border-color: var(--pixel-btn-primary-bg);
	background-color: rgba(90, 50, 163, 0.2);
	box-shadow: 0 3px 0 0 var(--pixel-btn-primary-shade);
	transform: translateY(-1px);
}

.option-tile.disabled {
	cursor: default;
}

.option-tile.is-correct-option {
	border-color: #10b981 !important;
	background-color: rgba(16, 185, 129, 0.15) !important;
	box-shadow: 0 3px 0 0 #065f46 !important;
}

.option-tile.is-wrong-marked {
	border-color: #ef4444 !important;
	background-color: rgba(239, 68, 68, 0.15) !important;
	box-shadow: 0 3px 0 0 #7f1d1d !important;
}

.result-indicator {
	width: 20px;
	height: 20px;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}

.neutral-dash {
	color: var(--pixel-text-dim);
	font-family: var(--font-pixel);
	font-size: 11px;
}

.option-prefix {
	font-family: var(--font-pixel);
	font-size: 13px;
	font-weight: 700;
	color: var(--pixel-text-muted);
	min-width: 20px;
	flex-shrink: 0;
}

.option-badges-wrap {
	margin-left: auto;
	display: flex;
	align-items: center;
	gap: 0.5rem;
	flex-shrink: 0;
}

.radio-indicator {
	width: 16px;
	height: 16px;
	border-radius: 2px;
	border: 2px solid var(--pixel-border);
	background-color: var(--pixel-bg-alt);
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}

.radio-indicator.checked {
	border-color: var(--pixel-btn-primary-bg);
	background-color: var(--pixel-btn-primary-shade);
}

.radio-dot {
	width: 6px;
	height: 6px;
	background-color: #fff;
	border-radius: 1px;
}

.option-text {
	font-size: 0.95rem;
	color: var(--pixel-text);
	line-height: 1.4;
}

.explanation-box {
	margin-top: 0.5rem;
}

.action-footer {
	padding: 0;
	margin-top: 0.5rem;
	background: transparent;
	border-top: none;
}

.completed-msg {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	font-family: var(--font-pixel);
	font-size: 12px;
	color: #34d399;
}

.incorrect-msg {
	color: #f87171 !important;
}

.empty-state {
	text-align: center;
	padding: 2.5rem 1rem;
	color: var(--pixel-text-dim);
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 0.5rem;
}
</style>
