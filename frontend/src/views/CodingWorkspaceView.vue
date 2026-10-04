<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vuestic-ui'
import api from '@/services/api'
import type { DailyChallengeData, CodingQuestionData, CodeSubmissionResult } from '@/types'
import { decodeHtmlEntities, formatDuration, getDifficultyColor } from '@/utils/text'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import CodeEditor from '@/components/student/CodeEditor.vue'
import TestcaseConsole from '@/components/student/TestcaseConsole.vue'

const route = useRoute()
const router = useRouter()
const { init: notify } = useToast()

const assignmentId = computed<number>(() => Number(route.params.assignmentId))

const isLoading = ref<boolean>(true)
const challenge = ref<DailyChallengeData | null>(null)
const codingQuestion = computed<CodingQuestionData | null>(() => challenge.value?.coding_question || null)

// Resizable splitter model values (percentages)
const horizontalSplit = ref<number>(40) // 40% left pane, 60% right pane
const verticalSplit = ref<number>(60) // 60% editor, 40% console
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

const defaultStarterTemplates: Record<string, string> = {
	python: `# Write your solution here
class Solution:
    def solve(self, *args):
        pass
`,
	cpp: `#include <iostream>
#include <vector>
#include <string>

using namespace std;

class Solution {
public:
    int solve() {
        return 0;
    }
};
`,
	java: `import java.util.*;

public class Solution {
    public int solve() {
        return 0;
    }
}
`,
	c: `#include <stdio.h>
#include <stdlib.h>

int solve() {
    return 0;
}
`,
}

const activeStarterTemplates = computed<Record<string, string>>(() => {
	if (codingQuestion.value?.starter_templates && Object.keys(codingQuestion.value.starter_templates).length > 0) {
		return { ...defaultStarterTemplates, ...codingQuestion.value.starter_templates }
	}
	return defaultStarterTemplates
})

function initStarterCode(): void {
	const templates = activeStarterTemplates.value
	const lang = selectedLanguage.value
	if (!languageCodes.value[lang]) {
		const initialCode = templates[lang] || defaultStarterTemplates[lang] || ''
		languageCodes.value[lang] = initialCode
		sourceCode.value = initialCode
	} else {
		sourceCode.value = languageCodes.value[lang]!
	}
}

function handleLanguageChange(newLang: string): void {
	const lang = String(newLang).toLowerCase()
	const targetLang = lang === 'c++' ? 'cpp' : lang
	if (targetLang === selectedLanguage.value) return

	// Save current code for current language
	languageCodes.value[selectedLanguage.value] = sourceCode.value
	selectedLanguage.value = targetLang

	// Retrieve code for new language, or fallback to starter template
	if (languageCodes.value[targetLang] !== undefined) {
		sourceCode.value = languageCodes.value[targetLang]!
	} else {
		const template = activeStarterTemplates.value[targetLang] || defaultStarterTemplates[targetLang] || ''
		languageCodes.value[targetLang] = template
		sourceCode.value = template
	}
}

function handleResetCode(): void {
	const template = activeStarterTemplates.value[selectedLanguage.value] || defaultStarterTemplates[selectedLanguage.value] || ''
	sourceCode.value = template
	languageCodes.value[selectedLanguage.value] = template
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
		// 1. Fetch assignment details
		const res = await api.get<DailyChallengeData>(`/student/daily/assignment/${assignmentId.value}`)
		if (res.success && res.data) {
			challenge.value = res.data
			submissionAttempts.value = res.data.submission_attempts_count ?? 0

			// 2. Start or resume coding session
			if (res.data.coding_status === 'solved') {
				elapsedSeconds.value = res.data.coding_time_spent_seconds ?? 0
			} else {
				// Call backend start-session to get or resume start timestamp
				const sessRes = await api.post<{
					coding_started_at: string
					elapsed_seconds: number
					submission_attempts_count: number
				}>(
					'/student/daily/coding-session/start',
					{ assignment_id: assignmentId.value }
				)
				if (sessRes.success && sessRes.data) {
					submissionAttempts.value = sessRes.data.submission_attempts_count ?? 0
					elapsedSeconds.value = Math.max(sessRes.data.elapsed_seconds ?? 0, 0)
				} else if (res.data.elapsed_seconds !== undefined && res.data.elapsed_seconds !== null) {
					elapsedSeconds.value = Math.max(res.data.elapsed_seconds, 0)
				}
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
				<VaButton
					preset="plain"
					icon="arrow_back"
					size="small"
					class="back-btn"
					@click="router.push('/student')"
				>
					Daily Challenge
				</VaButton>
				<VaBadge
					v-if="challenge?.coding_status === 'solved'"
					text="SOLVED"
					color="success"
					size="small"
				/>
			</div>

			<div class="topbar-center">
				<!-- Live Session Stopwatch Timer -->
				<div class="timer-badge" :title="isTimerRunning ? 'Coding Session Active' : 'Session Stopped'">
					<VaIcon name="timer" size="small" :color="isTimerRunning ? 'primary' : 'secondary'" />
					<span class="timer-digits">{{ formatDuration(elapsedSeconds) }}</span>
				</div>

				<!-- Submission Attempts -->
				<div class="attempts-badge" title="Submission Attempts">
					<VaIcon name="history" size="small" />
					<span>Attempts: {{ submissionAttempts }}</span>
				</div>
			</div>

			<div class="topbar-right">
				<VaButton
					preset="secondary"
					size="small"
					icon="play_arrow"
					:loading="isRunning"
					:disabled="isSubmitting"
					class="run-action-btn"
					@click="handleRun"
				>
					Run (Sample Cases)
				</VaButton>

				<VaButton
					size="small"
					icon="cloud_upload"
					:loading="isSubmitting"
					:disabled="isRunning"
					class="submit-action-btn"
					@click="handleSubmit"
				>
					Submit Solution
				</VaButton>
			</div>
		</header>

		<!-- Main Resizable Workspace (Left: Problem Specs, Right: Editor + Console) -->
		<main class="workspace-viewport">
			<VaSplit
				v-model="horizontalSplit"
				:limits="[20, 20]"
				class="horizontal-split-container"
			>
				<!-- LEFT PANE: Problem Description & Constraints (No redundant sample cases) -->
				<template #start>
					<div class="problem-pane">
						<div class="pane-content-scroll">
							<div class="problem-header-section">
								<h1 class="pane-problem-title">{{ codingQuestion?.title }}</h1>
								<div class="pane-tags-row">
									<VaBadge
										v-if="codingQuestion?.difficulty"
										:text="codingQuestion.difficulty.toUpperCase()"
										:color="getDifficultyColor(codingQuestion.difficulty)"
									/>
									<VaBadge text="+30 XP" color="primary" />
									<VaBadge :text="`${codingQuestion?.time_limit_ms ?? 2000} ms`" color="backgroundElement" />
									<VaBadge :text="`${Math.round((codingQuestion?.memory_limit_kb ?? 128000) / 1024)} MB`" color="backgroundElement" />
								</div>
							</div>

							<VaDivider class="pane-divider" />

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
						<VaSplit
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
						</VaSplit>
					</div>
				</template>
			</VaSplit>
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
	background: var(--va-background-primary);
}

.workspace-topbar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	height: 48px;
	padding: 0 1rem;
	background: var(--va-background-secondary);
	border-bottom: 1px solid var(--va-background-border);
	flex-shrink: 0;
	z-index: 10;
}

.topbar-left {
	display: flex;
	align-items: center;
	gap: 0.65rem;
}

.back-btn {
	color: var(--va-text-primary);
	font-weight: 600;
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
	background: var(--va-background-primary);
	border: 1px solid var(--va-background-border);
	border-radius: 14px;
	font-size: 0.8rem;
	font-weight: 600;
	color: var(--va-text-primary);
}

.timer-digits {
	font-family: 'JetBrains Mono', monospace !important;
}

.topbar-right {
	display: flex;
	align-items: center;
	gap: 0.65rem;
}

.run-action-btn {
	font-weight: 600;
}

.submit-action-btn {
	font-weight: 600;
}

.workspace-viewport {
	flex: 1;
	min-height: 0;
	min-width: 0;
	height: calc(100vh - 48px);
	overflow: hidden;
}

.horizontal-split-container {
	height: 100%;
	width: 100%;
}

.problem-pane {
	height: 100%;
	overflow-y: auto;
	background: var(--va-background-primary);
	border-right: 1px solid var(--va-background-border);
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
	font-size: 1.35rem;
	font-weight: 800;
	margin: 0;
	color: var(--va-text-primary);
}

.pane-tags-row {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	flex-wrap: wrap;
}

.pane-divider {
	margin: 0.25rem 0;
}

.section-heading {
	font-size: 0.95rem;
	font-weight: 700;
	color: var(--va-text-primary);
	margin-bottom: 0.5rem;
}

.constraints-box {
	margin: 0;
	padding: 0.75rem 1rem;
	background: var(--va-background-secondary);
	border: 1px solid var(--va-background-border);
	border-radius: 6px;
	font-family: 'JetBrains Mono', monospace !important;
	font-size: 0.85rem;
	white-space: pre-wrap;
	color: var(--va-text-primary);
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

/* Custom Splitter Handles */
:deep(.va-split__dragger) {
	z-index: 10;
	background: var(--va-background-border);
	transition: background 0.15s ease;
}

:deep(.va-split--horizontal > .va-split__dragger) {
	width: 6px !important;
	cursor: col-resize;
}

:deep(.va-split--horizontal > .va-split__dragger:hover),
:deep(.va-split--horizontal > .va-split__dragger:active) {
	background: var(--va-primary) !important;
}

:deep(.va-split--vertical > .va-split__dragger) {
	height: 6px !important;
	cursor: row-resize;
}

:deep(.va-split--vertical > .va-split__dragger:hover),
:deep(.va-split--vertical > .va-split__dragger:active) {
	background: var(--va-primary) !important;
}
</style>
