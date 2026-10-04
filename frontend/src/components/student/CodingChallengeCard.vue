<script setup lang="ts">
import { ref } from 'vue'
import type { DailyChallengeData, CodingQuestionData, CodeSubmissionResult } from '@/types'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'

const props = defineProps<{
	challenge: DailyChallengeData | null
	codingQuestion: CodingQuestionData | null
	executionResult: CodeSubmissionResult | null
	securityError: string | null
	isSubmitting: boolean
	isRunning?: boolean
}>()

const emit = defineEmits<{
	(e: 'run', payload: { language: string; sourceCode: string }): void
	(e: 'submit', payload: { language: string; sourceCode: string }): void
}>()

const selectedLanguage = ref<string>('python')
const sourceCode = ref<string>('')

const languageOptions = [
	{ label: 'Python 3', value: 'python' },
	{ label: 'C++ 17', value: 'cpp' },
	{ label: 'Java 17', value: 'java' },
	{ label: 'C', value: 'c' },
]

const starterTemplates: Record<string, string> = {
	python: `# Write your solution here
def solve():
    # Read input from stdin
    # Write output to stdout
    pass

if __name__ == '__main__':
    solve()
`,
	cpp: `#include <iostream>
using namespace std;

int main() {
    // Fast I/O
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    // Read input and solve
    return 0;
}
`,
	java: `import java.util.Scanner;

public class Solution {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        // Solve problem
    }
}
`,
	c: `#include <stdio.h>

int main() {
    // Solve problem
    return 0;
}
`,
}

function handleLanguageChange(): void {
	if (!sourceCode.value.trim() || Object.values(starterTemplates).includes(sourceCode.value)) {
		sourceCode.value = starterTemplates[selectedLanguage.value] || ''
	}
}

function handleEditorKeydown(e: KeyboardEvent): void {
	if (e.key === 'Tab') {
		e.preventDefault()
		const target = e.target as HTMLTextAreaElement
		const start = target.selectionStart
		const end = target.selectionEnd
		sourceCode.value = sourceCode.value.substring(0, start) + '    ' + sourceCode.value.substring(end)
		setTimeout(() => {
			target.selectionStart = target.selectionEnd = start + 4
		}, 0)
	}
}

function handleRun(): void {
	emit('run', { language: selectedLanguage.value, sourceCode: sourceCode.value })
}

function handleSubmit(): void {
	emit('submit', { language: selectedLanguage.value, sourceCode: sourceCode.value })
}
</script>

<template>
	<VaCard class="challenge-card">
		<VaCardTitle class="card-header-row">
			<div class="question-meta-group">
				<VaBadge color="primary" text="DAILY CODING PROBLEM" />
				<VaBadge
					v-if="codingQuestion?.difficulty"
					:color="codingQuestion.difficulty === 'hard' ? 'danger' : codingQuestion.difficulty === 'medium' ? 'warning' : 'success'"
					:text="codingQuestion.difficulty.toUpperCase()"
				/>
			</div>
		</VaCardTitle>

		<VaCardContent>
			<div v-if="codingQuestion" class="coding-body">
				<h3 class="problem-title">{{ codingQuestion.title }}</h3>
				<div class="problem-statement">
					<MarkdownRenderer :content="codingQuestion.word_problem_text" />
				</div>

				<VaCard v-if="codingQuestion.constraints_text" color="backgroundPrimary" class="constraints-panel">
					<VaCardContent>
						<h4 class="section-label">Constraints</h4>
						<pre class="constraints-text">{{ codingQuestion.constraints_text }}</pre>
					</VaCardContent>
				</VaCard>

				<!-- Sample Test Cases -->
				<div v-if="codingQuestion.sample_test_cases.length > 0" class="samples-wrapper">
					<h4 class="section-label">Sample Test Cases</h4>
					<VaCard
						v-for="(tc, idx) in codingQuestion.sample_test_cases"
						:key="idx"
						color="backgroundPrimary"
						class="sample-case-box"
					>
						<VaCardContent>
							<div class="sample-head">
								<VaBadge :text="`Sample Case #${idx + 1}`" color="backgroundElement" />
							</div>
							<div class="sample-grid">
								<div class="sample-item">
									<span class="sample-header">Input:</span>
									<pre class="sample-code">{{ tc.input_data }}</pre>
								</div>
								<div class="sample-item">
									<span class="sample-header">Expected Output:</span>
									<pre class="sample-code">{{ tc.expected_output }}</pre>
								</div>
							</div>
						</VaCardContent>
					</VaCard>
				</div>

				<!-- Code Editor Area -->
				<div class="editor-section">
					<div class="editor-toolbar">
						<div class="lang-selector-group">
							<VaSelect
								v-model="selectedLanguage"
								:options="languageOptions"
								label="Language"
								value-by="value"
								text-by="label"
								class="lang-select-control"
								@update:modelValue="handleLanguageChange"
							/>
						</div>
						<span class="editor-hint">Press Tab for code indentation</span>
					</div>

					<VaTextarea
						v-model="sourceCode"
						class="code-textarea"
						placeholder="Write your solution here..."
						autosize
						:min-rows="14"
						@keydown="handleEditorKeydown"
					/>

					<div class="editor-actions">
						<div class="status-indicator-area">
							<span v-if="challenge?.coding_status === 'solved'" class="solved-indicator">
								<VaIcon name="check_circle" color="success" /> Problem Solved (+30 XP)
							</span>
						</div>

						<div class="btn-group">
							<VaButton
								preset="secondary"
								:loading="isRunning"
								icon="play_arrow"
								class="run-btn"
								@click="handleRun"
							>
								Run (Sample Cases)
							</VaButton>

							<VaButton
								:loading="isSubmitting"
								icon="cloud_upload"
								class="submit-btn"
								@click="handleSubmit"
							>
								Submit Solution
							</VaButton>
						</div>
					</div>

					<!-- Security Alert Box -->
					<VaAlert
						v-if="securityError"
						color="danger"
						border="top"
						class="security-alert"
					>
						<template #icon>
							<VaIcon name="warning" />
						</template>
						<strong>Security Policy Violation:</strong> {{ securityError }}
					</VaAlert>

					<!-- Execution Feedback Console -->
					<VaCard v-if="executionResult" color="backgroundPrimary" class="execution-console">
						<VaCardContent>
							<div class="console-header">
								<div class="console-title-group">
									<span class="console-title">{{ executionResult.mode === 'run' ? 'Sample Cases Test Run' : 'Submission Evaluation' }}</span>
									<span v-if="executionResult.mode === 'run'" class="console-sub-note">Executed against 3 sample test cases only. Not counted as solved.</span>
									<span v-else-if="executionResult.phase === 'sample'" class="console-sub-note error-note">Failed on sample test cases.</span>
									<span v-else-if="executionResult.phase === 'hidden'" class="console-sub-note error-note">Sample cases passed, but failed on hidden standard validation cases.</span>
									<span v-else-if="executionResult.ai_flagged" class="console-sub-note warning-note">Code flagged by AI Academic Integrity Review.</span>
									<span v-else-if="executionResult.execution_status === 'passed'" class="console-sub-note success-note">All 13 test cases passed & AI verified! Solution accepted.</span>
								</div>
								<VaBadge
									:color="executionResult.execution_status === 'passed' ? 'success' : (executionResult.ai_flagged ? 'warning' : 'danger')"
									:text="executionResult.execution_status === 'passed' ? (executionResult.mode === 'run' ? 'SAMPLE PASSED' : 'ACCEPTED') : (executionResult.ai_flagged ? 'FLAGGED' : 'FAILED')"
								/>
							</div>

							<div class="console-metrics">
								<VaBadge
									color="backgroundElement"
									:text="`Test Cases: ${executionResult.test_cases_passed} / ${executionResult.test_cases_total}`"
								/>
								<VaBadge
									v-if="executionResult.runtime_ms"
									color="backgroundElement"
									:text="`Time: ${executionResult.runtime_ms}ms`"
								/>
								<VaBadge
									v-if="executionResult.memory_kb"
									color="backgroundElement"
									:text="`Memory: ${Math.round(executionResult.memory_kb / 1000)}MB`"
								/>
							</div>

							<div v-if="executionResult.ai_flagged" class="output-block error-block">
								<span class="output-label error-label">Academic Integrity Review:</span>
								<pre class="output-text error-text">{{ executionResult.ai_review_notes || 'Suspicious shortcut or hardcoded output pattern detected. Please submit a general algorithmic implementation.' }}</pre>
							</div>

							<div v-if="executionResult.compiler_output" class="output-block">
								<span class="output-label">Standard Output:</span>
								<pre class="output-text">{{ executionResult.compiler_output }}</pre>
							</div>

							<div v-if="executionResult.error_message" class="output-block error-block">
								<span class="output-label error-label">Feedback / Diagnostics:</span>
								<pre class="output-text error-text">{{ executionResult.error_message }}</pre>
							</div>
						</VaCardContent>
					</VaCard>
				</div>
			</div>

			<div v-else class="empty-state">
				<VaIcon name="inbox" size="48px" color="secondary" class="empty-icon" />
				<p>No coding challenge assigned for today yet.</p>
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
	gap: 0.75rem;
}

.problem-title {
	font-size: 1.25rem;
	font-weight: 700;
	color: var(--va-text-primary);
	margin: 0 0 0.75rem;
}

.problem-statement {
	color: var(--va-text-primary);
	line-height: 1.6;
	font-size: 0.95rem;
}

.section-label {
	font-size: 0.8rem;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 0.04em;
	color: var(--va-text-secondary);
	margin: 0 0 0.5rem;
}

.constraints-panel {
	border: 1px solid var(--va-background-border);
	margin-top: 1rem;
}

.constraints-text {
	margin: 0;
	font-family: 'JetBrains Mono', monospace !important;
	font-size: 0.85rem;
	white-space: pre-wrap;
	color: var(--va-text-primary);
}

.samples-wrapper {
	display: flex;
	flex-direction: column;
	gap: 0.75rem;
	margin-top: 1rem;
}

.sample-case-box {
	border: 1px solid var(--va-background-border);
}

.sample-head {
	margin-bottom: 0.5rem;
}

.sample-grid {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 1rem;
}

@media (max-width: 640px) {
	.sample-grid {
		grid-template-columns: 1fr;
	}
}

.sample-header {
	font-size: 0.75rem;
	font-weight: 600;
	color: var(--va-text-secondary);
}

.sample-code {
	background: var(--va-background-element);
	color: var(--va-text-primary);
	padding: 0.5rem;
	margin: 0.25rem 0 0;
	font-size: 0.85rem;
	font-family: 'JetBrains Mono', monospace !important;
	white-space: pre-wrap;
}

.editor-section {
	margin-top: 1.5rem;
	border-top: 1px solid var(--va-background-border);
	padding-top: 1.25rem;
}

.editor-toolbar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	flex-wrap: wrap;
	gap: 0.75rem;
	margin-bottom: 0.75rem;
}

.lang-selector-group {
	min-width: 160px;
}

.editor-hint {
	font-size: 0.75rem;
	color: var(--va-text-secondary);
}

.code-textarea {
	width: 100%;
	font-family: 'JetBrains Mono', monospace !important;
	font-size: 0.9rem;
	line-height: 1.5;
}

.editor-actions {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-top: 0.75rem;
	flex-wrap: wrap;
	gap: 0.75rem;
}

.btn-group {
	display: flex;
	align-items: center;
	gap: 0.75rem;
}

.solved-indicator {
	color: var(--va-success);
	font-weight: 600;
	font-size: 0.9rem;
	display: inline-flex;
	align-items: center;
	gap: 0.35rem;
}

.security-alert {
	margin-top: 1rem;
}

.execution-console {
	margin-top: 1.25rem;
	border: 1px solid var(--va-background-border);
}

.console-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 0.75rem;
	flex-wrap: wrap;
	gap: 0.5rem;
}

.console-title-group {
	display: flex;
	flex-direction: column;
	gap: 0.2rem;
}

.console-title {
	font-weight: 700;
	font-size: 0.92rem;
	color: var(--va-text-primary);
}

.console-sub-note {
	font-size: 0.75rem;
	color: var(--va-text-secondary);
}

.error-note {
	color: var(--va-danger);
	font-weight: 600;
}

.warning-note {
	color: var(--va-warning);
	font-weight: 600;
}

.success-note {
	color: var(--va-success);
	font-weight: 600;
}

.console-metrics {
	display: flex;
	gap: 0.5rem;
	margin-bottom: 0.75rem;
	flex-wrap: wrap;
}

.output-block {
	margin-top: 0.5rem;
}

.output-label {
	font-size: 0.75rem;
	font-weight: 600;
	color: var(--va-text-secondary);
}

.error-label {
	color: var(--va-danger);
}

.output-text {
	background: var(--va-background-element);
	color: var(--va-text-primary);
	border: 1px solid var(--va-background-border);
	padding: 0.75rem;
	font-size: 0.85rem;
	font-family: 'JetBrains Mono', monospace !important;
	margin: 0.25rem 0 0;
	white-space: pre-wrap;
	max-height: 160px;
	overflow-y: auto;
}

.error-text {
	color: var(--va-danger);
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
