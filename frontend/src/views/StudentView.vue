<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePixelToast } from '@/components/pixel/usePixelToast'

import api from '@/services/api'
import type { DailyChallengeData, ProgressData } from '@/types'
import { getDifficultyColor } from '@/utils/text'
import DailyFocusBanner from '@/components/student/DailyFocusBanner.vue'
import McqChallengeCard from '@/components/student/McqChallengeCard.vue'
import PixelCard from '@/components/pixel/PixelCard.vue'
import PixelCardTitle from '@/components/pixel/PixelCardTitle.vue'
import PixelCardContent from '@/components/pixel/PixelCardContent.vue'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelButton from '@/components/pixel/PixelButton.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'

const router = useRouter()
const authStore = useAuthStore()
const { init: notify } = usePixelToast()

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
      },
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

      <!-- 2. Daily Coding Challenge Overview Card -->
      <section class="flow-section">
        <PixelCard class="coding-overview-card">
          <PixelCardTitle class="coding-card-header">
            <div class="coding-meta-badges">
              <span class="card-type-title">CODING PROBLEM</span>
              <PixelBadge
                v-if="challenge?.coding_question?.difficulty"
                :text="challenge.coding_question.difficulty.toUpperCase()"
                :color="getDifficultyColor(challenge.coding_question.difficulty)"
              />
              <PixelBadge text="+30 XP" color="primary" />
            </div>

            <PixelBadge
              v-if="challenge?.coding_status === 'solved'"
              text="COMPLETED"
              color="success"
            />
          </PixelCardTitle>

          <PixelCardContent>
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
                    <PixelIcon name="check" :size="14" color="#34d399" /> Problem Solved (+30 XP)
                  </span>
                  <span v-else class="pending-tag">
                    <PixelIcon name="clock" :size="14" /> Ready to solve
                  </span>
                </div>

                <PixelButton
                  color="primary"
                  size="medium"
                  icon="code"
                  class="solve-action-btn"
                  @click="goToCodingWorkspace"
                >
                  {{ challenge.coding_status === 'solved' ? 'Review Code' : 'Enter Workspace' }}
                </PixelButton>
              </div>
            </div>

            <div v-else class="empty-coding-state">
              <PixelSprite name="sword" :size="36" class="empty-icon" />
              <p>No coding question assigned for today yet.</p>
            </div>
          </PixelCardContent>
        </PixelCard>
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

.card-type-title {
  font-family: var(--font-pixel);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--pixel-text);
  line-height: 1;
}

.coding-overview-body {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding: 0.25rem 0;
}

.problem-display-title {
  font-family: var(--font-pixel);
  font-size: 1.35rem;
  color: var(--pixel-text);
  margin: 0 0 0.4rem;
}

.problem-subtitle {
  font-size: 0.95rem;
  color: var(--pixel-text-muted);
  margin: 0;
}

.coding-action-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 1rem;
  border-top: 2px solid var(--pixel-border);
  flex-wrap: wrap;
  gap: 1rem;
}

.status-indicator {
  display: flex;
  align-items: center;
  font-family: var(--font-pixel);
  font-size: 12px;
}

.solved-tag {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: #34d399;
}

.pending-tag {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--pixel-text-dim);
}

.empty-coding-state {
  text-align: center;
  padding: 2.5rem 1rem;
  color: var(--pixel-text-dim);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}
</style>
