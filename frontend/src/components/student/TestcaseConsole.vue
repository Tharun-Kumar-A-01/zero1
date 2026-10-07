<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { SampleTestCase, CodeSubmissionResult, TestCaseResultItem } from '@/types'
import { decodeHtmlEntities } from '@/utils/text'

const props = defineProps<{
	sampleTestCases: SampleTestCase[]
	executionResult: CodeSubmissionResult | null
	isRunning?: boolean
	isSubmitting?: boolean
	isCollapsed?: boolean
}>()

const emit = defineEmits<{
	(e: 'update:isCollapsed', val: boolean): void
}>()

const activeMainTab = ref<'testcases' | 'result'>('testcases')
const selectedCaseIndex = ref<number>(0)
const selectedResultCaseIndex = ref<number>(0)

const activeSampleCase = computed<SampleTestCase | null>(() => {
	if (!props.sampleTestCases || props.sampleTestCases.length === 0) return null
	return props.sampleTestCases[selectedCaseIndex.value] || props.sampleTestCases[0] || null
})

const hasResultCases = computed<boolean>(() => {
	return Boolean(props.executionResult?.test_case_results && props.executionResult.test_case_results.length > 0)
})

const activeResultCase = computed<TestCaseResultItem | null>(() => {
	const list = props.executionResult?.test_case_results
	if (!list || list.length === 0) return null
	return list[selectedResultCaseIndex.value] || list[0] || null
})

function formatStatusName(status: string): string {
	const s = (status || '').toLowerCase()
	if (s === 'passed') return 'Accepted'
	if (s === 'failed') return 'Wrong Answer'
	if (s === 'compilation_error') return 'Compilation Error'
	if (s === 'timeout') return 'Time Limit Exceeded'
	if (s === 'memory_exceeded') return 'Memory Limit Exceeded'
	if (s === 'error') return 'Runtime Error'
	return s.replace(/_/g, ' ').toUpperCase()
}

watch(
	() => props.executionResult,
	(newRes) => {
		if (newRes && newRes.test_case_results && newRes.test_case_results.length > 0) {
			const firstFailed = newRes.test_case_results.findIndex((c) => c.status !== 'passed')
			selectedResultCaseIndex.value = firstFailed >= 0 ? firstFailed : 0
		} else {
			selectedResultCaseIndex.value = 0
		}
	},
	{ immediate: true }
)

function toggleCollapse(): void {
	emit('update:isCollapsed', !props.isCollapsed)
}

function switchToResultTab(): void {
	activeMainTab.value = 'result'
}

defineExpose({
	switchToResultTab,
})
</script>

<template>
	<div class="testcase-console" :class="{ 'is-collapsed': isCollapsed }">
		<!-- Console Header / Bar -->
		<div class="console-header">
			<div class="header-tabs">
				<button
					type="button"
					class="tab-btn"
					:class="{ active: activeMainTab === 'testcases' }"
					@click="activeMainTab = 'testcases'"
				>
					<VaIcon name="data_object" size="small" />
					<span>Testcase</span>
				</button>

				<button
					type="button"
					class="tab-btn"
					:class="{ active: activeMainTab === 'result' }"
					@click="activeMainTab = 'result'"
				>
					<VaIcon name="terminal" size="small" />
					<span>Test Result</span>
					<span
						v-if="executionResult"
						class="status-indicator-dot"
						:class="executionResult.execution_status === 'passed' ? 'dot-success' : 'dot-danger'"
					/>
				</button>
			</div>

			<div class="header-actions">
				<VaButton
					preset="plain"
					size="small"
					:icon="isCollapsed ? 'expand_less' : 'expand_more'"
					:title="isCollapsed ? 'Expand console' : 'Collapse console'"
					@click="toggleCollapse"
				>
					{{ isCollapsed ? 'Console' : '' }}
				</VaButton>
			</div>
		</div>

		<!-- Console Content (Hidden if collapsed) -->
		<div v-show="!isCollapsed" class="console-content">
			<!-- TAB 1: Sample Testcases -->
			<div v-if="activeMainTab === 'testcases'" class="cases-panel">
				<div class="case-selector-pills">
					<button
						v-for="(tc, idx) in sampleTestCases"
						:key="tc.id || idx"
						type="button"
						class="pill-btn"
						:class="{ active: selectedCaseIndex === idx }"
						@click="selectedCaseIndex = idx"
					>
						Case {{ idx + 1 }}
					</button>
				</div>

				<div v-if="activeSampleCase" class="case-details">
					<div class="io-group">
						<span class="io-label">Input</span>
						<pre class="io-pre">{{ decodeHtmlEntities(activeSampleCase.input_data) }}</pre>
					</div>

					<div class="io-group">
						<span class="io-label">Expected Output</span>
						<pre class="io-pre">{{ decodeHtmlEntities(activeSampleCase.expected_output) }}</pre>
					</div>
				</div>

				<div v-else class="empty-cases">
					<span>No sample test cases available.</span>
				</div>
			</div>

			<!-- TAB 2: Execution Results -->
			<div v-else class="result-panel">
				<!-- Running / Submitting Spinner -->
				<div v-if="isRunning || isSubmitting" class="executing-state">
					<VaProgressCircle indeterminate size="medium" />
					<span class="executing-text">
						{{ isSubmitting ? 'Evaluating solution against 3 sample & 10 hidden test cases...' : 'Executing sample test cases on sandbox...' }}
					</span>
				</div>

				<!-- Execution Result Present -->
				<div v-else-if="executionResult" class="result-details">
					<!-- Verdict Header Banner -->
					<div class="verdict-banner" :class="executionResult.execution_status === 'passed' ? 'verdict-pass' : 'verdict-fail'">
						<div class="verdict-title-row">
							<VaIcon
								:name="executionResult.execution_status === 'passed' ? 'check_circle' : 'cancel'"
								size="medium"
							/>
							<span class="verdict-title">
								{{ formatStatusName(executionResult.execution_status) }}
							</span>
						</div>

						<div class="verdict-stats-row">
							<span v-if="executionResult.runtime_ms !== undefined && executionResult.runtime_ms !== null" class="stat-badge">
								Runtime: <strong>{{ executionResult.runtime_ms }} ms</strong>
							</span>
							<span v-if="executionResult.memory_kb !== undefined && executionResult.memory_kb !== null" class="stat-badge">
								Memory: <strong>{{ executionResult.memory_kb }} KB</strong>
							</span>
							<span class="stat-badge">
								Passed: <strong>{{ executionResult.test_cases_passed }} / {{ executionResult.test_cases_total }}</strong>
							</span>
						</div>
					</div>

					<!-- Global Error Alert (when no detailed test cases or overall fatal error) -->
					<VaAlert
						v-if="executionResult.error_message && (!hasResultCases || !activeResultCase?.error_message)"
						color="danger"
						class="error-alert"
					>
						{{ executionResult.error_message }}
					</VaAlert>

					<!-- Compiler Output -->
					<div v-if="executionResult.compiler_output" class="io-group">
						<span class="io-label error-label">Compiler Output</span>
						<pre class="io-pre error-pre">{{ executionResult.compiler_output }}</pre>
					</div>

					<!-- Detailed Test Case Breakdown (Case 1, Case 2, Case 3) -->
					<div v-if="hasResultCases && executionResult.test_case_results" class="result-breakdown-section">
						<!-- Result Case Selector Pills -->
						<div class="case-selector-pills result-pills-row">
							<button
								v-for="(tc, idx) in executionResult.test_case_results"
								:key="tc.case_number || idx"
								type="button"
								class="pill-btn result-pill-btn"
								:class="{
									active: selectedResultCaseIndex === idx,
									'pill-passed': tc.status === 'passed',
									'pill-failed': tc.status !== 'passed'
								}"
								@click="selectedResultCaseIndex = idx"
							>
								<VaIcon
									:name="tc.status === 'passed' ? 'check' : 'close'"
									size="14px"
									class="pill-status-icon"
								/>
								<span>Case {{ tc.case_number || (idx + 1) }}</span>
							</button>
						</div>

						<!-- Selected Result Case Breakdown -->
						<div v-if="activeResultCase" class="case-details result-case-details">
							<!-- Status & Timing Header -->
							<div class="result-status-tag-row">
								<span
									class="case-status-tag"
									:class="activeResultCase.status === 'passed' ? 'tag-passed' : 'tag-failed'"
								>
									{{ formatStatusName(activeResultCase.status) }}
								</span>
								<span v-if="activeResultCase.runtime_ms !== undefined && activeResultCase.runtime_ms !== null" class="case-meta-tag">
									{{ activeResultCase.runtime_ms }} ms
								</span>
							</div>

							<!-- Case Error / Traceback if any -->
							<div v-if="activeResultCase.error_message" class="io-group">
								<span class="io-label error-label">Error / Traceback</span>
								<pre class="io-pre error-pre">{{ activeResultCase.error_message }}</pre>
							</div>

							<!-- Case Input -->
							<div class="io-group">
								<span class="io-label">Input</span>
								<pre class="io-pre">{{ decodeHtmlEntities(activeResultCase.input) || '(empty input)' }}</pre>
							</div>

							<!-- Case Expected Output -->
							<div class="io-group">
								<span class="io-label">Expected Output</span>
								<pre class="io-pre expected-pre">{{ decodeHtmlEntities(activeResultCase.expected_output) }}</pre>
							</div>

							<!-- Case Actual Output -->
							<div class="io-group">
								<span class="io-label">Your Output (Actual)</span>
								<pre
									class="io-pre"
									:class="activeResultCase.status === 'passed' ? 'match-pre' : 'mismatch-pre'"
								>{{ decodeHtmlEntities(activeResultCase.actual_output) || '(no output produced)' }}</pre>
							</div>
						</div>
					</div>

					<!-- Hidden Testcase Notification for Submissions -->
					<VaAlert
						v-if="executionResult.phase === 'hidden' && executionResult.execution_status !== 'passed'"
						color="warning"
						outline
						class="hidden-notice"
					>
						Passed all 3 sample test cases, but failed on hidden test cases ({{ executionResult.test_cases_passed }} / {{ executionResult.test_cases_total }} passed). Hidden test case inputs and expected outputs are confidential to prevent hardcoded solutions.
					</VaAlert>

					<!-- Anti-Cheat Status Alert -->
					<VaAlert
						v-if="executionResult.ai_flagged"
						color="danger"
						icon="warning"
						class="anticheat-alert"
					>
						<strong>AI Integrity Review:</strong> {{ executionResult.ai_review_notes }}
					</VaAlert>
				</div>

				<!-- No result yet -->
				<div v-else class="empty-result">
					<VaIcon name="play_arrow" size="32px" color="secondary" />
					<p>Run or Submit your solution to inspect test results.</p>
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped>
.testcase-console {
	display: flex;
	flex-direction: column;
	height: 100%;
	width: 100%;
	background: var(--va-background-secondary);
	border-top: 1px solid var(--va-background-border);
	overflow: hidden;
	transition: max-height 0.2s ease;
}

.testcase-console.is-collapsed {
	height: 42px !important;
}

.console-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0 0.75rem;
	height: 42px;
	background: var(--va-background-primary);
	border-bottom: 1px solid var(--va-background-border);
	flex-shrink: 0;
	user-select: none;
}

.header-tabs {
	display: flex;
	align-items: center;
	gap: 0.25rem;
}

.tab-btn {
	display: inline-flex;
	align-items: center;
	gap: 0.4rem;
	padding: 0.4rem 0.75rem;
	border: none;
	background: transparent;
	color: var(--va-text-secondary);
	font-size: 0.85rem;
	font-weight: 600;
	cursor: pointer;
	border-radius: 4px;
	transition: all 0.15s ease;
}

.tab-btn:hover {
	color: var(--va-text-primary);
	background: var(--va-background-element);
}

.tab-btn.active {
	color: var(--va-primary);
	background: var(--va-background-secondary);
}

.status-indicator-dot {
	width: 8px;
	height: 8px;
	border-radius: 50%;
}

.dot-success {
	background: var(--va-success);
}

.dot-danger {
	background: var(--va-danger);
}

.console-content {
	flex-grow: 1;
	overflow-y: auto;
	padding: 0.85rem;
	font-size: 0.88rem;
}

.cases-panel {
	display: flex;
	flex-direction: column;
	gap: 0.85rem;
}

.case-selector-pills {
	display: flex;
	gap: 0.5rem;
	flex-wrap: wrap;
}

.pill-btn {
	display: inline-flex;
	align-items: center;
	gap: 0.35rem;
	padding: 0.35rem 0.85rem;
	border: 1px solid var(--va-background-border);
	background: var(--va-background-primary);
	color: var(--va-text-primary);
	border-radius: 14px;
	font-size: 0.8rem;
	font-weight: 500;
	cursor: pointer;
	transition: all 0.15s ease;
}

.pill-btn:hover {
	border-color: var(--va-primary);
}

.pill-btn.active {
	background: var(--va-primary);
	color: var(--va-text-inverted);
	border-color: var(--va-primary);
}

.result-pill-btn.pill-passed {
	border-color: rgba(var(--va-success-rgb, 40, 167, 69), 0.4);
}

.result-pill-btn.pill-passed .pill-status-icon {
	color: var(--va-success);
}

.result-pill-btn.pill-failed {
	border-color: rgba(var(--va-danger-rgb, 220, 53, 69), 0.4);
}

.result-pill-btn.pill-failed .pill-status-icon {
	color: var(--va-danger);
}

.result-pill-btn.active.pill-passed {
	background: var(--va-success);
	color: #fff;
	border-color: var(--va-success);
}

.result-pill-btn.active.pill-passed .pill-status-icon {
	color: #fff;
}

.result-pill-btn.active.pill-failed {
	background: var(--va-danger);
	color: #fff;
	border-color: var(--va-danger);
}

.result-pill-btn.active.pill-failed .pill-status-icon {
	color: #fff;
}

.case-details {
	display: flex;
	flex-direction: column;
	gap: 0.75rem;
}

.result-breakdown-section {
	display: flex;
	flex-direction: column;
	gap: 0.85rem;
	margin-top: 0.5rem;
	border-top: 1px solid var(--va-background-border);
	padding-top: 0.85rem;
}

.result-status-tag-row {
	display: flex;
	align-items: center;
	gap: 0.65rem;
}

.case-status-tag {
	font-size: 0.78rem;
	font-weight: 700;
	padding: 0.2rem 0.6rem;
	border-radius: 4px;
	text-transform: uppercase;
	letter-spacing: 0.03em;
}

.tag-passed {
	background: rgba(var(--va-success-rgb, 40, 167, 69), 0.15);
	color: var(--va-success);
	border: 1px solid var(--va-success);
}

.tag-failed {
	background: rgba(var(--va-danger-rgb, 220, 53, 69), 0.15);
	color: var(--va-danger);
	border: 1px solid var(--va-danger);
}

.case-meta-tag {
	font-size: 0.78rem;
	color: var(--va-text-secondary);
}

.io-group {
	display: flex;
	flex-direction: column;
	gap: 0.35rem;
}

.io-label {
	font-size: 0.75rem;
	font-weight: 600;
	text-transform: uppercase;
	color: var(--va-text-secondary);
	letter-spacing: 0.04em;
}

.io-label.error-label {
	color: var(--va-danger);
}

.io-pre {
	margin: 0;
	padding: 0.65rem 0.85rem;
	background: var(--va-background-primary);
	border: 1px solid var(--va-background-border);
	border-radius: 6px;
	font-family: 'JetBrains Mono', monospace !important;
	font-variant-ligatures: none !important;
	-webkit-font-variant-ligatures: none !important;
	font-feature-settings: 'liga' 0, 'calt' 0, 'dlig' 0 !important;
	font-size: 0.85rem;
	white-space: pre-wrap;
	word-break: break-all;
	color: var(--va-text-primary);
}

.expected-pre {
	border-left: 3px solid var(--va-info);
}

.match-pre {
	border-left: 3px solid var(--va-success);
	background: rgba(var(--va-success-rgb, 40, 167, 69), 0.06);
}

.mismatch-pre {
	border-left: 3px solid var(--va-danger);
	background: rgba(var(--va-danger-rgb, 220, 53, 69), 0.06);
	color: var(--va-danger);
}

.error-pre {
	color: var(--va-danger);
	border-left: 3px solid var(--va-danger);
	border-color: var(--va-danger);
	background: rgba(var(--va-danger-rgb, 220, 53, 69), 0.08);
}

.error-alert {
	margin-top: 0.25rem;
}

.hidden-notice {
	margin-top: 0.5rem;
}

.result-panel {
	display: flex;
	flex-direction: column;
	gap: 0.85rem;
}

.executing-state {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 1rem;
	padding: 2.5rem 1rem;
	color: var(--va-text-secondary);
}

.verdict-banner {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0.75rem 1rem;
	border-radius: 6px;
	flex-wrap: wrap;
	gap: 0.75rem;
}

.verdict-pass {
	background: rgba(var(--va-success-rgb, 40, 167, 69), 0.12);
	color: var(--va-success);
	border: 1px solid var(--va-success);
}

.verdict-fail {
	background: rgba(var(--va-danger-rgb, 220, 53, 69), 0.12);
	color: var(--va-danger);
	border: 1px solid var(--va-danger);
}

.verdict-title-row {
	display: flex;
	align-items: center;
	gap: 0.5rem;
}

.verdict-title {
	font-size: 1.1rem;
	font-weight: 700;
}

.verdict-stats-row {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	font-size: 0.85rem;
}

.stat-badge {
	background: var(--va-background-primary);
	padding: 0.25rem 0.5rem;
	border-radius: 4px;
	border: 1px solid var(--va-background-border);
	color: var(--va-text-primary);
}

.empty-cases,
.empty-result {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 2.5rem 1rem;
	color: var(--va-text-secondary);
	gap: 0.5rem;
	text-align: center;
}
</style>
