<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from 'vuestic-ui'

import api from '@/services/api'
import type { DailyChallengeData, ProgressData } from '@/types'
import { getDifficultyColor } from '@/utils/text'
import DailyFocusBanner from '@/components/student/DailyFocusBanner.vue'
import McqChallengeCard from '@/components/student/McqChallengeCard.vue'

const router = useRouter()
const authStore = useAuthStore()
const { init: notify } = useToast()

const isLoading = ref<boolean>(true)
const challenge = ref<DailyChallengeData | null>(null)
const progress = ref<ProgressData | null>(null)

// MCQ state
const isSubmittingMcq = ref<boolean>(false)
const mcqExplanation = ref<string | null>(null)

async function fetchDailyChallenge(): Promise<void> {
	try {
		const res = await api.get<DailyChallengeData>('/student/daily/today')
		if (res.success && res.data) {
			challenge.value = res.data
		}
	} catch {
		notify({ color: 'warning', message: 'Could not load today challenge.' })
	}
}

async function fetchProgress(): Promise<void> {
	try {
		const res = await api.get<ProgressData>('/student/progress')
		if (res.success && res.data) {
			progress.value = res.data
		}
	} catch {
		// Silent error
	}
}

async function handleMcqSubmit(selectedOption: number): Promise<void> {
	if (!challenge.value) return
	isSubmittingMcq.value = true
	try {
		const res = await api.post<{ is_correct: boolean; explanation?: string; points_awarded: number; current_streak: number; is_day_solved: boolean }>(
			'/student/daily/mcq-submit',
			{
				assignment_id: challenge.value.id,
				selected_option_index: selectedOption,
			}
		)

		if (res.success && res.data) {
			challenge.value.mcq_status = res.data.is_correct ? 'correct' : 'incorrect'
			mcqExplanation.value = res.data.explanation || null
			if (res.data.is_correct) {
				notify({ color: 'success', message: `Correct Answer! +${res.data.points_awarded} Points awarded.` })
			} else {
				notify({ color: 'danger', message: 'Incorrect. Review the question and try again.' })
			}
			await fetchProgress()
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Could not submit answer.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Network error' })
	} finally {
		isSubmittingMcq.value = false
	}
}

function goToCodingWorkspace(): void {
	if (challenge.value) {
		router.push(`/workspace/coding/${challenge.value.id}`)
	}
}

onMounted(async (): Promise<void> => {
	await Promise.all([fetchDailyChallenge(), fetchProgress()])
	isLoading.value = false
})
</script>

<template>
	<div class="student-page">
		<DailyFocusBanner
			:challenge="challenge"
			:studentName="authStore.user?.name || 'Student'"
		/>

		<div class="challenges-flow">
			<!-- 1. Aptitude MCQ Challenge Card -->
			<section class="flow-section">
				<McqChallengeCard
					:challenge="challenge"
					:mcq="challenge?.mcq_question || null"
					:explanation="mcqExplanation"
					:isSubmitting="isSubmittingMcq"
					@submit="handleMcqSubmit"
				/>
			</section>

			<!-- 2. Daily Coding Challenge Overview Card (Compact: Title, XP, Difficulty & Solve Button) -->
			<section class="flow-section">
				<VaCard class="coding-overview-card">
					<VaCardTitle class="coding-card-header">
						<div class="coding-meta-badges">
							<VaBadge text="DAILY CODING PROBLEM" color="primary">
								<template #prepend>
									<VaIcon name="code" size="small" />
								</template>
							</VaBadge>
							<VaBadge
								v-if="challenge?.coding_question?.difficulty"
								:text="challenge.coding_question.difficulty.toUpperCase()"
								:color="getDifficultyColor(challenge.coding_question.difficulty)"
							/>
							<VaBadge text="+30 XP" color="warning" />
						</div>

						<VaBadge
							v-if="challenge?.coding_status === 'solved'"
							text="COMPLETED"
							color="success"
						/>
					</VaCardTitle>

					<VaCardContent>
						<div v-if="challenge?.coding_question" class="coding-overview-body">
							<div class="problem-intro">
								<h3 class="problem-display-title">{{ challenge.coding_question.title }}</h3>
								<p class="problem-subtitle">
									Solve today's coding problem using your preferred language in the dedicated coding workspace.
								</p>
							</div>

							<div class="coding-action-row">
								<div class="status-indicator">
									<span v-if="challenge.coding_status === 'solved'" class="solved-tag">
										<VaIcon name="check_circle" color="success" /> Problem Solved (+30 XP)
									</span>
									<span v-else class="pending-tag">
										<VaIcon name="schedule" color="secondary" /> Ready to solve
									</span>
								</div>

								<VaButton
									icon="code"
									size="medium"
									class="solve-action-btn"
									@click="goToCodingWorkspace"
								>
									{{ challenge.coding_status === 'solved' ? 'Review Code' : 'Solve Problem' }}
								</VaButton>
							</div>
						</div>

						<div v-else class="empty-coding-state">
							<VaIcon name="code_off" size="36px" color="secondary" />
							<p>No coding question assigned for today yet.</p>
						</div>
					</VaCardContent>
				</VaCard>
			</section>
		</div>
	</div>
</template>

<style scoped>
.student-page {
	max-width: 1000px;
	margin: 0 auto;
	padding: 1.5rem;
	width: 100%;
}

.challenges-flow {
	display: flex;
	flex-direction: column;
	gap: 1.5rem;
}

.flow-section {
	width: 100%;
}

.coding-overview-card {
	border: 1px solid var(--va-background-border);
}

.coding-card-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	flex-wrap: wrap;
	gap: 0.75rem;
}

.coding-meta-badges {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	flex-wrap: wrap;
}

.coding-overview-body {
	display: flex;
	flex-direction: column;
	gap: 1.25rem;
	padding: 0.5rem 0;
}

.problem-display-title {
	font-size: 1.35rem;
	font-weight: 800;
	color: var(--va-text-primary);
	margin: 0 0 0.4rem;
}

.problem-subtitle {
	font-size: 0.95rem;
	color: var(--va-text-secondary);
	margin: 0;
}

.coding-action-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding-top: 0.75rem;
	border-top: 1px solid var(--va-background-border);
	flex-wrap: wrap;
	gap: 1rem;
}

.status-indicator {
	display: flex;
	align-items: center;
	font-size: 0.9rem;
	font-weight: 600;
}

.solved-tag {
	display: flex;
	align-items: center;
	gap: 0.4rem;
	color: var(--va-success);
}

.pending-tag {
	display: flex;
	align-items: center;
	gap: 0.4rem;
	color: var(--va-text-secondary);
}

.solve-action-btn {
	font-weight: 700;
}

.empty-coding-state {
	text-align: center;
	padding: 2.5rem 1rem;
	color: var(--va-text-secondary);
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 0.5rem;
}
</style>
