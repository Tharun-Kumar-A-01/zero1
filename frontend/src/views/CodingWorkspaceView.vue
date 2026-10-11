<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePixelToast } from '@/components/pixel/usePixelToast'
import api from '@/services/api'
import type { DailyChallengeData, CodingQuestionData, CodeSubmissionResult } from '@/types'
import { decodeHtmlEntities, formatDuration, getDifficultyColor } from '@/utils/text'
import { getProblemStarterTemplates } from '@/utils/boilerplate'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import CodeEditor from '@/components/student/CodeEditor.vue'
import TestcaseConsole from '@/components/student/TestcaseConsole.vue'
import PixelButton from '@/components/pixel/PixelButton.vue'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'
import PixelSplit from '@/components/pixel/PixelSplit.vue'

const route = useRoute()
const router = useRouter()
const { init: notify } = usePixelToast()

const assignmentId = computed<number>(() => Number(route.params.assignmentId))

const isLoading = ref<boolean>(true)
const challenge = ref<DailyChallengeData | null>(null)
const codingQuestion = computed<CodingQuestionData | null>(() => challenge.value?.coding_question || null)

// Resizable splitter model values (percentages)
const horizontalSplit = ref<number>(40)
const verticalSplit = ref<number>(60)
const isConsoleCollapsed = ref<boolean>(false)

// Editor state with per-language code cache
const selectedLanguage = ref<string>('python')
const sourceCode = ref<string>('')
const languageCodes = ref<Record<string, string>>({})

// Execution state
const isRunning = ref<boolean>(false)
const isSubmitting = ref<boolean>(false)
const executionResult = ref<CodeSubmissionResult | null>(null)
const testcaseConsoleRef = ref<InstanceType<typeof TestcaseConsole> | null>(null)

// Session Timer & Attempts Tracking
const elapsedSeconds = ref<number>(0)
const isTimerRunning = ref<boolean>(false)
let timerInterval: ReturnType<typeof setInterval> | null = null
const submissionAttempts = ref<number>(0)

const activeStarterTemplates = computed<Record<string, string>>(() => {
  const q = codingQuestion.value
  if (!q) return {}
  return getProblemStarterTemplates(
    q.title,
    q.function_name,
    q.parameter_definitions,
    q.return_type,
    q.sample_test_cases,
    q.starter_templates,
    q.word_problem_text,
  )
})

watch(
  () => codingQuestion.value,
  (q) => {
    if (q) {
      const templates = activeStarterTemplates.value
      const lang = selectedLanguage.value
      const isStaticOrEmpty =
        !sourceCode.value ||
        sourceCode.value.includes('def solve(self, *args):') ||
        sourceCode.value.includes('int solve() {\n        return 0;\n    }')
      if (isStaticOrEmpty && templates[lang]) {
        sourceCode.value = templates[lang]
        languageCodes.value[lang] = templates[lang]
      }
    }
  },
  { immediate: true },
)

function initStarterCode(): void {
  const templates = activeStarterTemplates.value
  const lang = selectedLanguage.value
  if (languageCodes.value[lang]) {
    sourceCode.value = languageCodes.value[lang]
  } else if (templates[lang]) {
    sourceCode.value = templates[lang]
    languageCodes.value[lang] = templates[lang]
  } else {
    sourceCode.value = ''
  }
}

function handleLanguageChange(newLang: string): void {
  languageCodes.value[selectedLanguage.value] = sourceCode.value
  selectedLanguage.value = newLang
  const templates = activeStarterTemplates.value
  if (languageCodes.value[newLang]) {
    sourceCode.value = languageCodes.value[newLang]
  } else if (templates[newLang]) {
    sourceCode.value = templates[newLang]
    languageCodes.value[newLang] = templates[newLang]
  } else {
    sourceCode.value = ''
  }
}

function handleResetCode(): void {
  const templates = activeStarterTemplates.value
  const lang = selectedLanguage.value
  if (templates[lang]) {
    sourceCode.value = templates[lang]
    languageCodes.value[lang] = templates[lang]
    notify({ color: 'info', message: `Reset ${lang.toUpperCase()} code to starter boilerplate.` })
  }
}

function startTimer(): void {
  if (isTimerRunning.value) return
  isTimerRunning.value = true
  timerInterval = setInterval(() => {
    elapsedSeconds.value++
  }, 1000)
}

function stopTimer(): void {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
  isTimerRunning.value = false
}

async function loadAssignmentAndStartSession(): Promise<void> {
  isLoading.value = true
  try {
    const res = await api.get<DailyChallengeData>(`/student/daily/assignment/${assignmentId.value}`)
    if (res.success && res.data) {
      challenge.value = res.data

      if (res.data.coding_time_spent_seconds && res.data.coding_time_spent_seconds > 0) {
        elapsedSeconds.value = res.data.coding_time_spent_seconds
      }

      if (res.data.coding_status !== 'solved') {
        startTimer()
      }

      initStarterCode()
    } else {
      notify({ color: 'danger', message: res.error?.message || 'Could not load coding challenge.' })
    }
  } catch (err: unknown) {
    notify({ color: 'danger', message: err instanceof Error ? err.message : 'Network error' })
  } finally {
    isLoading.value = false
  }
}

async function handleRun(): Promise<void> {
  if (!sourceCode.value.trim()) {
    notify({ color: 'warning', message: 'Please write your solution code before running.' })
    return
  }

  isRunning.value = true
  isConsoleCollapsed.value = false
  testcaseConsoleRef.value?.switchToResultTab()

  try {
    const res = await api.post<CodeSubmissionResult>('/student/daily/code-run', {
      assignment_id: assignmentId.value,
      language: selectedLanguage.value,
      source_code: sourceCode.value,
    })

    if (res.success && res.data) {
      executionResult.value = res.data
      if (res.data.execution_status === 'passed') {
        notify({ color: 'success', message: 'All sample test cases passed!' })
      } else {
        notify({ color: 'warning', message: res.data.error_message || 'Sample test case failed.' })
      }
    } else {
      notify({ color: 'danger', message: res.error?.message || 'Execution error.' })
    }
  } catch (err: unknown) {
    notify({ color: 'danger', message: err instanceof Error ? err.message : 'Execution failed.' })
  } finally {
    isRunning.value = false
  }
}

async function handleSubmit(): Promise<void> {
  if (!sourceCode.value.trim()) {
    notify({ color: 'warning', message: 'Please write your solution code before submitting.' })
    return
  }

  isSubmitting.value = true
  isConsoleCollapsed.value = false
  testcaseConsoleRef.value?.switchToResultTab()

  try {
    const res = await api.post<CodeSubmissionResult>('/student/daily/code-submit', {
      assignment_id: assignmentId.value,
      language: selectedLanguage.value,
      source_code: sourceCode.value,
    })

    if (res.success && res.data) {
      executionResult.value = res.data
      submissionAttempts.value = res.data.submission_attempts_count ?? submissionAttempts.value + 1

      if (res.data.execution_status === 'passed') {
        stopTimer()
        if (challenge.value) {
          challenge.value.coding_status = 'solved'
          challenge.value.coding_time_spent_seconds = res.data.coding_time_spent_seconds ?? elapsedSeconds.value
        }
        notify({
          color: 'success',
          message: `Problem Solved! +${res.data.points_awarded ?? 30} XP awarded.`,
        })
      } else if (res.data.ai_flagged) {
        notify({ color: 'danger', message: `Academic Integrity Warning: ${res.data.ai_review_notes}` })
      } else {
        notify({ color: 'danger', message: res.data.error_message || 'Submission failed.' })
      }
    } else {
      notify({ color: 'danger', message: res.error?.message || 'Submission error.' })
    }
  } catch (err: unknown) {
    notify({ color: 'danger', message: err instanceof Error ? err.message : 'Network error' })
  } finally {
    isSubmitting.value = false
  }
}

onMounted(() => {
  loadAssignmentAndStartSession()
})

onUnmounted(() => {
  stopTimer()
})
</script>

<template>
  <div class="coding-workspace-layout">
    <!-- Top Bar: Back, Timer, Attempts, Run, Submit -->
    <header class="workspace-topbar">
      <div class="topbar-left">
        <PixelButton
          color="secondary"
          size="small"
          icon="arrow-left"
          class="back-btn"
          @click="router.push('/student')"
        >
          Daily Challenge
        </PixelButton>
        <PixelBadge
          v-if="challenge?.coding_status === 'solved'"
          text="SOLVED"
          color="success"
        />
      </div>

      <div class="topbar-center">
        <!-- Live Session Stopwatch Timer -->
        <div class="timer-badge" :title="isTimerRunning ? 'Coding Session Active' : 'Session Stopped'">
          <PixelIcon name="clock" :size="14" :color="isTimerRunning ? 'var(--pixel-btn-primary-bg)' : 'var(--pixel-text-dim)'" />
          <span class="timer-digits">{{ formatDuration(elapsedSeconds) }}</span>
        </div>

        <!-- Submission Attempts -->
        <div class="attempts-badge" title="Submission Attempts">
          <PixelIcon name="refresh" :size="14" />
          <span>Attempts: {{ submissionAttempts }}</span>
        </div>
      </div>

      <div class="topbar-right">
        <PixelButton
          color="secondary"
          size="small"
          icon="play"
          :loading="isRunning"
          :disabled="isSubmitting"
          class="run-action-btn"
          @click="handleRun"
        >
          Run (Sample Cases)
        </PixelButton>

        <PixelButton
          color="primary"
          size="small"
          icon="upload"
          :loading="isSubmitting"
          :disabled="isRunning"
          class="submit-action-btn"
          @click="handleSubmit"
        >
          Submit Solution
        </PixelButton>
      </div>
    </header>

    <!-- Main Resizable Workspace (Left: Problem Specs, Right: Editor + Console) -->
    <main class="workspace-viewport">
      <PixelSplit
        v-model="horizontalSplit"
        :limits="[20, 20]"
        class="horizontal-split-container"
      >
        <!-- LEFT PANE: Problem Description & Constraints -->
        <template #start>
          <div class="problem-pane">
            <div class="pane-content-scroll">
              <div class="problem-header-section">
                <h1 class="pane-problem-title">{{ codingQuestion?.title }}</h1>
                <div class="pane-tags-row">
                  <PixelBadge
                    v-if="codingQuestion?.difficulty"
                    :text="codingQuestion.difficulty.toUpperCase()"
                    :color="getDifficultyColor(codingQuestion.difficulty)"
                  />
                  <PixelBadge text="+30 XP" color="primary" />
                  <PixelBadge :text="`${codingQuestion?.time_limit_ms ?? 2000} ms`" color="secondary" />
                  <PixelBadge :text="`${Math.round((codingQuestion?.memory_limit_kb ?? 128000) / 1024)} MB`" color="secondary" />
                </div>
              </div>

              <div class="pane-divider" />

              <!-- Problem Statement -->
              <div class="problem-statement-section">
                <h3 class="section-heading">Description</h3>
                <MarkdownRenderer
                  v-if="codingQuestion?.word_problem_text"
                  :content="decodeHtmlEntities(codingQuestion.word_problem_text)"
                />
              </div>

              <!-- Constraints -->
              <div v-if="codingQuestion?.constraints_text" class="constraints-section">
                <h3 class="section-heading">Constraints</h3>
                <pre class="constraints-box">{{ decodeHtmlEntities(codingQuestion.constraints_text) }}</pre>
              </div>
            </div>
          </div>
        </template>

        <!-- RIGHT PANE: Code Editor & Collapsible Console -->
        <template #end>
          <div class="editor-console-pane">
            <PixelSplit
              v-model="verticalSplit"
              vertical
              :limits="[20, 20]"
              class="vertical-split-container"
            >
              <!-- Editor Top Split -->
              <template #start>
                <div class="editor-subpane">
                  <CodeEditor
                    v-model="sourceCode"
                    :language="selectedLanguage"
                    :allowed-languages="codingQuestion?.allowed_languages"
                    :starter-templates="activeStarterTemplates"
                    @update:language="handleLanguageChange"
                    @reset-code="handleResetCode"
                  />
                </div>
              </template>

              <!-- Console Bottom Split -->
              <template #end>
                <div class="console-subpane">
                  <TestcaseConsole
                    ref="testcaseConsoleRef"
                    v-model:is-collapsed="isConsoleCollapsed"
                    :sample-test-cases="codingQuestion?.sample_test_cases || []"
                    :execution-result="executionResult"
                    :is-running="isRunning"
                    :is-submitting="isSubmitting"
                  />
                </div>
              </template>
            </PixelSplit>
          </div>
        </template>
      </PixelSplit>
    </main>
  </div>
</template>

<style scoped>
.coding-workspace-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  box-sizing: border-box;
  background: var(--pixel-bg);
}

.workspace-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 1rem;
  background: var(--pixel-surface);
  border-bottom: 2px solid var(--pixel-border);
  box-shadow: 0 2px 0 0 var(--pixel-border-dark);
  flex-shrink: 0;
  z-index: 10;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.back-btn {
  font-family: var(--font-pixel);
}

.topbar-center {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.timer-badge,
.attempts-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.25rem 0.65rem;
  background: var(--pixel-bg-alt);
  border: 1px solid var(--pixel-border);
  border-radius: 3px;
  font-family: var(--font-pixel);
  font-size: 11px;
  color: var(--pixel-text);
}

.timer-digits {
  font-family: var(--font-mono) !important;
  color: #fbbf24;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.workspace-viewport {
  flex: 1;
  min-height: 0;
  min-width: 0;
  height: calc(100vh - 52px);
  overflow: hidden;
}

.horizontal-split-container {
  height: 100%;
  width: 100%;
}

.problem-pane {
  height: 100%;
  overflow-y: auto;
  background: var(--pixel-surface);
  border-right: 2px solid var(--pixel-border);
}

.pane-content-scroll {
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.problem-header-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.pane-problem-title {
  font-family: var(--font-pixel);
  font-size: 1.35rem;
  margin: 0;
  color: var(--pixel-text);
}

.pane-tags-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.pane-divider {
  height: 2px;
  background: var(--pixel-border);
  margin: 0.25rem 0;
}

.section-heading {
  font-family: var(--font-pixel);
  font-size: 13px;
  text-transform: uppercase;
  color: var(--pixel-text-muted);
  margin-bottom: 0.5rem;
}

.constraints-box {
  margin: 0;
  padding: 0.75rem 1rem;
  background: var(--pixel-bg-alt);
  border: 2px solid var(--pixel-border);
  border-radius: 3px;
  font-family: var(--font-mono) !important;
  font-size: 0.85rem;
  white-space: pre-wrap;
  color: var(--pixel-text);
}

.editor-console-pane {
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.vertical-split-container {
  height: 100%;
  width: 100%;
}

.editor-subpane {
  height: 100%;
  overflow: hidden;
}

.console-subpane {
  height: 100%;
  overflow: hidden;
}
</style>
