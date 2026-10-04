<script setup lang="ts">
import { ref } from 'vue'
import type { CodingQuestionItem } from '@/types'

defineProps<{
	visible: boolean
	question: CodingQuestionItem | null
	isGenerating: boolean
	generatedCases: Array<{ input: string; expected_output: string; rationale?: string }>
}>()

const emit = defineEmits<{
	(e: 'update:visible', val: boolean): void
	(e: 'generate'): void
	(e: 'accept', cases: Array<{ input: string; expected_output: string }>): void
}>()

const selectedIndices = ref<Set<number>>(new Set([0, 1, 2]))

function toggleSelect(index: number): void {
	if (selectedIndices.value.has(index)) {
		selectedIndices.value.delete(index)
	} else {
		selectedIndices.value.add(index)
	}
}

function handleAccept(cases: Array<{ input: string; expected_output: string }>): void {
	const accepted = cases.filter((_, idx) => selectedIndices.value.has(idx))
	emit('accept', accepted)
}
</script>

<template>
	<VaModal
		:model-value="visible"
		title="AI Stress-Test Case Generator"
		ok-text="Accept Selected Cases"
		cancel-text="Close"
		:hide-default-actions="true"
		@update:model-value="emit('update:visible', $event)"
	>
		<div class="stress-dialog-body">
			<div class="dialog-explainer">
				<p>
					Targeted Gemini 2.5 Pro reasoning automatically synthesizes boundary conditions,
					worst-case inputs, and edge traps to stress-test student solutions.
				</p>
			</div>

			<div class="generate-trigger-bar">
				<VaButton
					:loading="isGenerating"
					size="small"
					icon="auto_awesome"
					@click="emit('generate')"
				>
					Run AI Stress Analysis
				</VaButton>
			</div>

			<div v-if="generatedCases.length > 0" class="cases-results">
				<h4 class="cases-heading">Generated Boundary Candidates</h4>
				<VaList class="cases-list">
					<VaCard
						v-for="(tc, idx) in generatedCases"
						:key="idx"
						color="backgroundPrimary"
						class="generated-item"
					>
						<VaCardContent class="case-card-content">
							<div class="gen-header">
								<VaCheckbox
									:model-value="selectedIndices.has(idx)"
									:label="`Edge Case #${idx + 1}`"
									@update:model-value="toggleSelect(idx)"
								/>
								<span v-if="tc.rationale" class="gen-reason">{{ tc.rationale }}</span>
							</div>
							<div class="gen-io">
								<div class="io-col">
									<span>Input:</span>
									<code class="code-box">{{ tc.input }}</code>
								</div>
								<div class="io-col">
									<span>Expected Output:</span>
									<code class="code-box">{{ tc.expected_output }}</code>
								</div>
							</div>
						</VaCardContent>
					</VaCard>
				</VaList>
			</div>
		</div>

		<template #footer>
			<div class="modal-footer-actions">
				<VaButton preset="secondary" @click="emit('update:visible', false)">
					Cancel
				</VaButton>
				<VaButton
					v-if="generatedCases.length > 0"
					icon="check"
					@click="handleAccept(generatedCases)"
				>
					Accept ({{ selectedIndices.size }})
				</VaButton>
			</div>
		</template>
	</VaModal>
</template>

<style scoped>
.stress-dialog-body {
	display: flex;
	flex-direction: column;
	gap: 1rem;
	padding: 0.5rem 0;
}

.dialog-explainer p {
	font-size: 0.85rem;
	color: var(--va-text-secondary);
	margin: 0;
	line-height: 1.5;
}

.generate-trigger-bar {
	display: flex;
	justify-content: flex-end;
}

.cases-results {
	display: flex;
	flex-direction: column;
	gap: 0.75rem;
}

.cases-heading {
	font-size: 0.85rem;
	font-weight: 700;
	color: var(--va-text-primary);
	margin: 0;
}

.cases-list {
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
	max-height: 320px;
	overflow-y: auto;
}

.generated-item {
	border: 1px solid var(--va-background-border);
}

.case-card-content {
	padding: 0.75rem;
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
}

.gen-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	font-size: 0.8rem;
}

.gen-reason {
	color: var(--va-text-secondary);
	font-style: italic;
	font-size: 0.75rem;
}

.gen-io {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 0.75rem;
}

.io-col {
	display: flex;
	flex-direction: column;
	gap: 0.15rem;
}

.io-col span {
	font-size: 0.7rem;
	color: var(--va-text-secondary);
}

.code-box {
	background: var(--va-background-element);
	color: var(--va-text-primary);
	padding: 0.35rem 0.5rem;
	font-family: monospace;
	font-size: 0.8rem;
	white-space: pre-wrap;
}

.modal-footer-actions {
	display: flex;
	justify-content: flex-end;
	gap: 0.5rem;
}
</style>
