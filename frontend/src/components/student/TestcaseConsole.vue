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
	return Boolean(
		props.executionResult?.test_case_results &&
		props.executionResult.test_case_results.length > 0,
	)
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
	{ immediate: true },
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
					<PixelIcon name="code" :size="14" />
					<span>Testcase</span>
				</button>

				<button
					type="button"
					class="tab-btn"
					:class="{ active: activeMainTab === 'result' }"
					@click="activeMainTab = 'result'"
				>
					<PixelIcon name="terminal" :size="14" />
					<span>Test Result</span>
					<span
						v-if="executionResult"
						class="status-indicator-dot"
						:class="
							executionResult.execution_status === 'passed'
								? 'dot-success'
								: 'dot-danger'
						"
					/>
				</button>
			</div>

			<div class="header-actions">
				<PixelButton
					color="secondary"
					size="small"
					:icon="isCollapsed ? 'chevron-up' : 'chevron-down'"
					:title="isCollapsed ? 'Expand console' : 'Collapse console'"
					@click="toggleCollapse"
				>
					{{ isCollapsed ? 'Console' : '' }}
				</PixelButton>
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
						<pre class="io-pre">{{
							decodeHtmlEntities(activeSampleCase.input_data)
						}}</pre>
					</div>

					<div class="io-group">
						<span class="io-label">Expected Output</span>
						<pre class="io-pre">{{
							decodeHtmlEntities(activeSampleCase.expected_output)
						}}</pre>
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
					<PixelIcon name="refresh" class="spin" :size="24" />
					<span class="executing-text">
						{{
							isSubmitting
								? 'Evaluating solution against 3 sample & 10 hidden test cases...'
								: 'Executing sample test cases on sandbox...'
						}}
					</span>
				</div>

				<!-- Execution Result Present -->
				<div v-else-if="executionResult" class="result-details">
					<!-- Verdict Header Banner -->
					<div
						class="verdict-banner"
						:class="
							executionResult.execution_status === 'passed'
								? 'verdict-pass'
								: 'verdict-fail'
						"
					>
						<div class="verdict-title-row">
							<PixelIcon
								:name="
									executionResult.execution_status === 'passed'
										? 'check'
										: 'cross'
								"
								:size="20"
							/>
							<span class="verdict-title">
								{{ formatStatusName(executionResult.execution_status) }}
							</span>
						</div>

						<div class="verdict-stats-row">
							<span
								v-if="
									executionResult.runtime_ms !== undefined &&
									executionResult.runtime_ms !== null
								"
								class="stat-badge"
							>
								Runtime: <strong>{{ executionResult.runtime_ms }} ms</strong>
							</span>
							<span
								v-if="
									executionResult.memory_kb !== undefined &&
									executionResult.memory_kb !== null
								"
								class="stat-badge"
							>
								Memory: <strong>{{ executionResult.memory_kb }} KB</strong>
							</span>
							<span class="stat-badge">
								Passed:
								<strong
									>{{ executionResult.test_cases_passed }} /
									{{ executionResult.test_cases_total }}</strong
								>
							</span>
						</div>
					</div>

					<!-- Global Error Alert (when no detailed test cases or overall fatal error) -->
					<PixelAlert
						v-if="
							executionResult.error_message &&
							(!hasResultCases || !activeResultCase?.error_message)
						"
						color="danger"
						class="error-alert"
					>
						{{ executionResult.error_message }}
					</PixelAlert>

					<!-- Compiler Output -->
					<div v-if="executionResult.compiler_output" class="io-group">
						<span class="io-label error-label">Compiler Output</span>
						<pre class="io-pre error-pre">{{ executionResult.compiler_output }}</pre>
					</div>

					<!-- Detailed Test Case Breakdown (Case 1, Case 2, Case 3) -->
					<div
						v-if="hasResultCases && executionResult.test_case_results"
						class="result-breakdown-section"
					>
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
									'pill-failed': tc.status !== 'passed',
								}"
								@click="selectedResultCaseIndex = idx"
							>
								<PixelIcon
									:name="tc.status === 'passed' ? 'check' : 'cross'"
									:size="12"
									class="pill-status-icon"
								/>
								<span>Case {{ tc.case_number || idx + 1 }}</span>
							</button>
						</div>

						<!-- Selected Result Case Breakdown -->
						<div v-if="activeResultCase" class="case-details result-case-details">
							<!-- Status & Timing Header -->
							<div class="result-status-tag-row">
								<span
									class="case-status-tag"
									:class="
										activeResultCase.status === 'passed'
											? 'tag-passed'
											: 'tag-failed'
									"
								>
									{{ formatStatusName(activeResultCase.status) }}
								</span>
								<span
									v-if="
										activeResultCase.runtime_ms !== undefined &&
										activeResultCase.runtime_ms !== null
									"
									class="case-meta-tag"
								>
									{{ activeResultCase.runtime_ms }} ms
								</span>
							</div>

							<!-- Case Error / Traceback if any -->
							<div v-if="activeResultCase.error_message" class="io-group">
								<span class="io-label error-label">Error / Traceback</span>
								<pre class="io-pre error-pre">{{
									activeResultCase.error_message
								}}</pre>
							</div>

							<!-- Case Input -->
							<div class="io-group">
								<span class="io-label">Input</span>
								<pre class="io-pre">{{
									decodeHtmlEntities(activeResultCase.input) || '(empty input)'
								}}</pre>
							</div>

							<!-- Case Expected Output -->
							<div class="io-group">
								<span class="io-label">Expected Output</span>
								<pre class="io-pre expected-pre">{{
									decodeHtmlEntities(activeResultCase.expected_output)
								}}</pre>
							</div>

							<!-- Case Actual Output -->
							<div class="io-group">
								<span class="io-label">Your Output (Actual)</span>
								<pre
									class="io-pre"
									:class="
										activeResultCase.status === 'passed'
											? 'match-pre'
											: 'mismatch-pre'
									"
									>{{
										decodeHtmlEntities(activeResultCase.actual_output) ||
										'(no output produced)'
									}}</pre>
							</div>
						</div>
					</div>

					<!-- Hidden Testcase Notification for Submissions -->
					<PixelAlert
						v-if="
							executionResult.phase === 'hidden' &&
							executionResult.execution_status !== 'passed'
						"
						color="warning"
						outline
						class="hidden-notice"
					>
						Passed all 3 sample test cases, but failed on hidden test cases ({{
							executionResult.test_cases_passed
						}}
						/ {{ executionResult.test_cases_total }} passed). Hidden test case inputs
						and expected outputs are confidential to prevent hardcoded solutions.
					</PixelAlert>

					<!-- Anti-Cheat Status Alert -->
					<PixelAlert
						v-if="executionResult.ai_flagged"
						color="danger"
						icon="warning"
						class="anticheat-alert"
					>
						<strong>AI Integrity Review:</strong> {{ executionResult.ai_review_notes }}
					</PixelAlert>
				</div>

				<!-- No result yet -->
				<div v-else class="empty-result">
					<PixelIcon name="play" :size="28" color="var(--pixel-text-dim)" />
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
	background: var(--pixel-surface-alt);
	border-top: 2px solid var(--pixel-border);
	overflow: hidden;
	transition: max-height 0.2s ease;
	font-family: var(--font-body);
}

.testcase-console.is-collapsed {
	height: 44px !important;
}

.console-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0 0.75rem;
	height: 44px;
	background: var(--pixel-surface);
	border-bottom: 2px solid var(--pixel-border);
	flex-shrink: 0;
	user-select: none;
}

.header-tabs {
	display: flex;
	align-items: flex-end;
	gap: 6px;
	height: 100%;
}

.tab-btn {
	display: inline-flex;
	align-items: center;
	gap: 6px;
	padding: 7px 14px;
	border: 2px solid var(--pixel-border);
	border-bottom: none;
	border-radius: 4px 4px 0 0;
	background: var(--pixel-surface-alt);
	color: var(--pixel-text-muted);
	font-family: var(--font-pixel);
	font-size: 11px;
	text-transform: uppercase;
	letter-spacing: 0.04em;
	cursor: pointer;
	position: relative;
	margin-bottom: -2px;
	transition:
		color 0.1s ease,
		background-color 0.1s ease;
	z-index: 1;
}

.tab-btn:hover {
	color: var(--pixel-text);
	background: var(--pixel-surface);
}

.tab-btn.active {
	color: #ffffff;
	background: var(--pixel-bg);
	border-color: var(--pixel-border);
	border-top: 2px solid var(--pixel-btn-primary-bg);
	border-bottom: 2px solid var(--pixel-bg);
	z-index: 2;
}

.status-indicator-dot {
	width: 6px;
	height: 6px;
	border-radius: 0;
	display: inline-block;
}

.dot-success {
	background: #10b981;
	box-shadow: 0 0 0 1px #064e3b;
}

.dot-danger {
	background: #ef4444;
	box-shadow: 0 0 0 1px #7f1d1d;
}

.console-content {
	flex-grow: 1;
	overflow-y: auto;
	padding: 1rem;
	background: var(--pixel-bg);
	color: var(--pixel-text);
}

.cases-panel {
	display: flex;
	flex-direction: column;
	gap: 1rem;
}

.case-selector-pills {
	display: flex;
	gap: 8px;
	flex-wrap: wrap;
}

.pill-btn {
	display: inline-flex;
	align-items: center;
	gap: 6px;
	padding: 6px 12px;
	border: 2px solid var(--pixel-border);
	border-radius: 2px;
	background-color: var(--pixel-surface);
	color: var(--pixel-text-dim);
	font-family: var(--font-pixel);
	font-size: 11px;
	text-transform: uppercase;
	letter-spacing: 0.04em;
	box-shadow: 0 3px 0 0 var(--pixel-border-dark);
	cursor: pointer;
	user-select: none;
	transition:
		transform 0.08s ease,
		box-shadow 0.08s ease,
		background-color 0.1s ease;
}

.pill-btn:hover:not(:active) {
	background-color: var(--pixel-surface-alt);
	color: var(--pixel-text);
}

.pill-btn:active,
.pill-btn.active {
	transform: translateY(2px);
	box-shadow: 0 1px 0 0 var(--pixel-border-dark);
	background-color: var(--pixel-btn-primary-bg);
	border-color: var(--pixel-btn-primary-border);
	color: #ffffff;
}

.result-pill-btn.pill-passed {
	border-color: #10b981;
	box-shadow: 0 3px 0 0 #064e3b;
	color: #6ee7b7;
}

.result-pill-btn.pill-passed .pill-status-icon {
	color: #34d399;
}

.result-pill-btn.pill-failed {
	border-color: #ef4444;
	box-shadow: 0 3px 0 0 #7f1d1d;
	color: #fca5a5;
}

.result-pill-btn.pill-failed .pill-status-icon {
	color: #f87171;
}

.result-pill-btn.active.pill-passed {
	background-color: #064e3b;
	border-color: #10b981;
	box-shadow: 0 1px 0 0 #064e3b;
	color: #ffffff;
	transform: translateY(2px);
}

.result-pill-btn.active.pill-passed .pill-status-icon {
	color: #ffffff;
}

.result-pill-btn.active.pill-failed {
	background-color: #7f1d1d;
	border-color: #ef4444;
	box-shadow: 0 1px 0 0 #7f1d1d;
	color: #ffffff;
	transform: translateY(2px);
}

.result-pill-btn.active.pill-failed .pill-status-icon {
	color: #ffffff;
}

.case-details {
	display: flex;
	flex-direction: column;
	gap: 0.85rem;
}

.result-breakdown-section {
	display: flex;
	flex-direction: column;
	gap: 1rem;
	margin-top: 0.75rem;
	border-top: 2px solid var(--pixel-border);
	padding-top: 1rem;
}

.result-status-tag-row {
	display: flex;
	align-items: center;
	gap: 0.75rem;
}

.case-status-tag {
	font-family: var(--font-pixel);
	font-size: 11px;
	font-weight: normal;
	padding: 3px 8px;
	border-radius: 2px;
	text-transform: uppercase;
	letter-spacing: 0.04em;
	border: 2px solid;
}

.tag-passed {
	background-color: #12281e;
	color: #6ee7b7;
	border-color: #10b981;
	box-shadow: 0 2px 0 0 #064e3b;
}

.tag-failed {
	background-color: #2a1518;
	color: #fca5a5;
	border-color: #ef4444;
	box-shadow: 0 2px 0 0 #7f1d1d;
}

.case-meta-tag {
	font-family: var(--font-pixel);
	font-size: 11px;
	color: var(--pixel-text-dim);
}

.io-group {
	display: flex;
	flex-direction: column;
	gap: 0.4rem;
}

.io-label {
	font-family: var(--font-pixel);
	font-size: 11px;
	font-weight: normal;
	text-transform: uppercase;
	color: var(--pixel-text-dim);
	letter-spacing: 0.05em;
}

.io-label.error-label {
	color: #f87171;
}

.io-pre {
	margin: 0;
	padding: 10px 12px;
	background: var(--pixel-surface-alt);
	border: 2px solid var(--pixel-border);
	border-radius: 2px;
	box-shadow: inset 0 2px 0 0 rgba(0, 0, 0, 0.4);
	font-family: var(--font-mono) !important;
	font-variant-ligatures: none !important;
	-webkit-font-variant-ligatures: none !important;
	font-feature-settings:
		'liga' 0,
		'calt' 0,
		'dlig' 0 !important;
	font-size: 12px;
	line-height: 1.5;
	white-space: pre-wrap;
	word-break: break-all;
	color: var(--pixel-text);
}

.expected-pre {
	border-left: 4px solid #38bdf8;
}

.match-pre {
	border-left: 4px solid #10b981;
	background: rgba(16, 185, 129, 0.06);
}

.mismatch-pre {
	border: 2px solid #ef4444;
	border-left: 4px solid #ef4444;
	background: #241417;
	color: #fca5a5;
}

.error-pre {
	color: #fca5a5;
	border: 2px solid #ef4444;
	border-left: 4px solid #ef4444;
	background: #241417;
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
	gap: 1rem;
}

.executing-state {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 1rem;
	padding: 2.5rem 1rem;
	font-family: var(--font-pixel);
	font-size: 12px;
	color: var(--pixel-text-dim);
}

.verdict-banner {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 10px 14px;
	border-radius: 2px;
	border: 2px solid;
	flex-wrap: wrap;
	gap: 0.75rem;
}

.verdict-pass {
	background-color: #12281e;
	border-color: #10b981;
	box-shadow: 0 4px 0 0 #064e3b;
	color: #6ee7b7;
}

.verdict-fail {
	background-color: #2a1518;
	border-color: #ef4444;
	box-shadow: 0 4px 0 0 #7f1d1d;
	color: #fca5a5;
}

.verdict-title-row {
	display: flex;
	align-items: center;
	gap: 8px;
}

.verdict-title {
	font-family: var(--font-pixel);
	font-size: 14px;
	font-weight: normal;
	text-transform: uppercase;
	letter-spacing: 0.04em;
}

.verdict-stats-row {
	display: flex;
	align-items: center;
	gap: 8px;
	flex-wrap: wrap;
}

.stat-badge {
	display: inline-flex;
	align-items: center;
	gap: 4px;
	background: var(--pixel-surface);
	padding: 4px 8px;
	border-radius: 2px;
	border: 2px solid var(--pixel-border-dark);
	color: var(--pixel-text);
	font-family: var(--font-pixel);
	font-size: 11px;
}

.stat-badge strong {
	font-weight: normal;
	color: #fbbf24;
}

.empty-cases,
.empty-result {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 2.5rem 1rem;
	color: var(--pixel-text-muted);
	font-family: var(--font-pixel);
	font-size: 12px;
	gap: 0.75rem;
	text-align: center;
}
</style>
