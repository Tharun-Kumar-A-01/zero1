<script setup lang="ts">
import { ref } from 'vue'
import type { DailyChallengeData, CodingQuestionData, CodeSubmissionResult } from '@/types'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import PixelCard from '@/components/pixel/PixelCard.vue'
import PixelCardTitle from '@/components/pixel/PixelCardTitle.vue'
import PixelCardContent from '@/components/pixel/PixelCardContent.vue'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelButton from '@/components/pixel/PixelButton.vue'
import PixelSelect from '@/components/pixel/PixelSelect.vue'
import PixelTextarea from '@/components/pixel/PixelTextarea.vue'
import PixelAlert from '@/components/pixel/PixelAlert.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'

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
  <PixelCard class="challenge-card">
    <PixelCardTitle class="card-header-row">
      <div class="question-meta-group">
        <span class="card-type-title">CODING PROBLEM</span>
        <PixelBadge
          v-if="codingQuestion?.difficulty"
          :color="codingQuestion.difficulty === 'hard' ? 'danger' : codingQuestion.difficulty === 'medium' ? 'warning' : 'success'"
          :text="codingQuestion.difficulty.toUpperCase()"
        />
        <PixelBadge text="+30 XP" color="primary" />
      </div>
    </PixelCardTitle>

    <PixelCardContent>
      <div v-if="codingQuestion" class="coding-body">
        <h3 class="problem-title">{{ codingQuestion.title }}</h3>
        <div class="problem-statement">
          <MarkdownRenderer :content="codingQuestion.word_problem_text" />
        </div>

        <div v-if="codingQuestion.constraints_text" class="constraints-panel">
          <h4 class="section-label">Constraints</h4>
          <pre class="constraints-text">{{ codingQuestion.constraints_text }}</pre>
        </div>

        <!-- Sample Test Cases -->
        <div v-if="codingQuestion.sample_test_cases.length > 0" class="samples-wrapper">
          <h4 class="section-label">Sample Test Cases</h4>
          <div
            v-for="(tc, idx) in codingQuestion.sample_test_cases"
            :key="idx"
            class="sample-case-box"
          >
            <div class="sample-head">
              <PixelBadge :text="`Sample Case #${idx + 1}`" color="secondary" />
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
          </div>
        </div>

        <!-- Code Editor Area -->
        <div class="editor-section">
          <div class="editor-toolbar">
            <div class="lang-selector-group">
              <PixelSelect
                v-model="selectedLanguage"
                :options="languageOptions"
                label="Language"
                value-by="value"
                text-by="label"
                class="lang-select-control"
                @update:model-value="handleLanguageChange"
              />
            </div>
            <span class="editor-hint">Press Tab for code indentation</span>
          </div>

          <PixelTextarea
            v-model="sourceCode"
            class="code-textarea"
            placeholder="Write your solution here..."
            :rows="14"
            @keydown="handleEditorKeydown"
          />

          <div class="editor-actions">
            <div class="status-indicator-area">
              <span v-if="challenge?.coding_status === 'solved'" class="solved-indicator">
                <PixelIcon name="check" :size="14" color="#34d399" /> Problem Solved (+30 XP)
              </span>
            </div>

            <div class="btn-group">
              <PixelButton
                color="secondary"
                :loading="isRunning"
                icon="play"
                class="run-btn"
                @click="handleRun"
              >
                Run (Sample Cases)
              </PixelButton>

              <PixelButton
                color="primary"
                :loading="isSubmitting"
                icon="upload"
                class="submit-btn"
                @click="handleSubmit"
              >
                Submit Solution
              </PixelButton>
            </div>
          </div>

          <!-- Security Alert Box -->
          <PixelAlert
            v-if="securityError"
            color="danger"
            class="security-alert"
          >
            <strong>Security Policy Violation:</strong> {{ securityError }}
          </PixelAlert>

          <!-- Execution Feedback Console -->
          <div v-if="executionResult" class="execution-console">
            <div class="console-header">
              <div class="console-title-group">
                <span class="console-title">{{ executionResult.mode === 'run' ? 'Sample Cases Test Run' : 'Submission Evaluation' }}</span>
                <span v-if="executionResult.mode === 'run'" class="console-sub-note">Executed against 3 sample test cases only. Not counted as solved.</span>
                <span v-else-if="executionResult.phase === 'sample'" class="console-sub-note error-note">Failed on sample test cases.</span>
                <span v-else-if="executionResult.phase === 'hidden'" class="console-sub-note error-note">Sample cases passed, but failed on hidden standard validation cases.</span>
                <span v-else-if="executionResult.ai_flagged" class="console-sub-note warning-note">Code flagged by AI Academic Integrity Review.</span>
                <span v-else-if="executionResult.execution_status === 'passed'" class="console-sub-note success-note">All test cases passed & AI verified! Solution accepted.</span>
              </div>
              <PixelBadge
                :color="executionResult.execution_status === 'passed' ? 'success' : (executionResult.ai_flagged ? 'warning' : 'danger')"
                :text="executionResult.execution_status === 'passed' ? (executionResult.mode === 'run' ? 'SAMPLE PASSED' : 'ACCEPTED') : (executionResult.ai_flagged ? 'FLAGGED' : 'FAILED')"
              />
            </div>

            <div class="console-metrics">
              <PixelBadge
                color="secondary"
                :text="`Test Cases: ${executionResult.test_cases_passed} / ${executionResult.test_cases_total}`"
              />
              <PixelBadge
                v-if="executionResult.runtime_ms"
                color="secondary"
                :text="`Time: ${executionResult.runtime_ms}ms`"
              />
              <PixelBadge
                v-if="executionResult.memory_kb"
                color="secondary"
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
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <PixelSprite name="sword" :size="48" class="empty-icon" />
        <p>No coding challenge assigned for today yet.</p>
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
  gap: 0.75rem;
}

.card-type-title {
  font-family: var(--font-pixel);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--pixel-text);
  line-height: 1;
}

.coding-body {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.problem-title {
  font-family: var(--font-pixel);
  font-size: 1.35rem;
  color: var(--pixel-text);
  margin: 0;
}

.problem-statement {
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--pixel-text);
}

.constraints-panel {
  background-color: var(--pixel-bg-alt);
  border: 2px solid var(--pixel-border);
  border-radius: 4px;
  padding: 12px;
}

.section-label {
  font-family: var(--font-pixel);
  font-size: 12px;
  text-transform: uppercase;
  color: var(--pixel-text-muted);
  margin: 0 0 6px 0;
}

.constraints-text {
  font-family: var(--font-mono);
  font-size: 12px;
  margin: 0;
  white-space: pre-wrap;
  color: var(--pixel-text);
}

.samples-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sample-case-box {
  background-color: var(--pixel-bg-alt);
  border: 2px solid var(--pixel-border);
  border-radius: 4px;
  padding: 12px;
}

.sample-head {
  margin-bottom: 8px;
}

.sample-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

@media (max-width: 640px) {
  .sample-grid {
    grid-template-columns: 1fr;
  }
}

.sample-header {
  font-family: var(--font-pixel);
  font-size: 11px;
  color: var(--pixel-text-dim);
}

.sample-code {
  font-family: var(--font-mono);
  font-size: 12px;
  margin: 4px 0 0 0;
  padding: 6px 8px;
  background-color: var(--pixel-surface);
  border: 1px solid var(--pixel-border);
  border-radius: 2px;
  white-space: pre-wrap;
  color: var(--pixel-text);
}

.editor-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.lang-selector-group {
  width: 180px;
}

.editor-hint {
  font-size: 11px;
  color: var(--pixel-text-dim);
}

.editor-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}

.btn-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

@media (max-width: 640px) {
  .editor-toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .lang-selector-group {
    width: 100%;
  }

  .editor-hint {
    display: none;
  }

  .editor-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .btn-group {
    width: 100%;
  }

  .run-btn,
  .submit-btn {
    flex: 1;
    justify-content: center;
  }

  .console-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}

.solved-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-pixel);
  font-size: 12px;
  color: #34d399;
}

.security-alert {
  margin-top: 10px;
}

.execution-console {
  background-color: var(--pixel-bg-alt);
  border: 2px solid var(--pixel-border);
  border-radius: 4px;
  padding: 14px;
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.console-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.console-title {
  font-family: var(--font-pixel);
  font-size: 13px;
  color: var(--pixel-text);
}

.console-sub-note {
  font-size: 12px;
  color: var(--pixel-text-dim);
}

.console-sub-note.error-note {
  color: #ff8b8b;
}

.console-sub-note.warning-note {
  color: #fbbf24;
}

.console-sub-note.success-note {
  color: #34d399;
}

.console-metrics {
  display: flex;
  align-items: center;
  gap: 8px;
}

.output-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.output-label {
  font-family: var(--font-pixel);
  font-size: 11px;
  color: var(--pixel-text-dim);
}

.output-text {
  font-family: var(--font-mono);
  font-size: 12px;
  margin: 0;
  padding: 8px;
  background-color: var(--pixel-surface);
  border: 1px solid var(--pixel-border);
  border-radius: 2px;
  white-space: pre-wrap;
  color: var(--pixel-text);
}

.error-block .output-text {
  border-color: #b83333;
  color: #ff9e9e;
}

.empty-state {
  text-align: center;
  padding: 3rem 1.5rem;
  color: var(--pixel-text-dim);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}
</style>
