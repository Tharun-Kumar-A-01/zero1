<script setup lang="ts">
import { ref } from 'vue'
import type { CodingQuestionItem } from '@/types'
import PixelModal from '@/components/pixel/PixelModal.vue'
import PixelButton from '@/components/pixel/PixelButton.vue'
import PixelCard from '@/components/pixel/PixelCard.vue'
import PixelCardContent from '@/components/pixel/PixelCardContent.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'

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

const selectedIndices = ref<Set<number>>(new Set())

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
	<PixelModal
		:model-value="visible"
		title="AI Stress-Test Generator"
		max-width="640px"
		hide-default-actions
		@update:model-value="emit('update:visible', $event)"
	>
		<div class="stress-dialog-body">
			<div class="dialog-explainer">
				<p>
					AI reasoning automatically synthesizes boundary conditions, worst-case inputs,
					and edge traps to stress-test student solutions.
				</p>
			</div>

			<div class="generate-trigger-bar">
				<PixelButton
					:loading="isGenerating"
					color="primary"
					icon="auto_awesome"
					@click="emit('generate')"
				>
					Generate Test Cases
				</PixelButton>
			</div>

			<div v-if="generatedCases.length > 0" class="cases-results">
				<h4 class="cases-heading">Generated Boundary Candidates</h4>
				<div class="cases-list">
					<PixelCard
						v-for="(tc, idx) in generatedCases"
						:key="idx"
						class="generated-item"
					>
						<PixelCardContent class="case-card-content">
							<div class="gen-header">
								<label
									class="pixel-checkbox-label"
									@click.prevent="toggleSelect(idx)"
								>
									<span
										class="pixel-checkbox"
										:class="{ checked: selectedIndices.has(idx) }"
									>
										<PixelIcon
											v-if="selectedIndices.has(idx)"
											name="check"
											:size="12"
										/>
									</span>
									<span>Edge Case #{{ idx + 1 }}</span>
								</label>
								<span v-if="tc.rationale" class="gen-reason">{{
									tc.rationale
								}}</span>
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
						</PixelCardContent>
					</PixelCard>
				</div>
			</div>
		</div>

		<template #footer>
			<div class="modal-footer-actions">
				<PixelButton color="secondary" @click="emit('update:visible', false)">
					Cancel
				</PixelButton>
				<PixelButton
					v-if="generatedCases.length > 0"
					color="primary"
					icon="check"
					@click="handleAccept(generatedCases)"
				>
					Accept ({{ selectedIndices.size }})
				</PixelButton>
			</div>
		</template>
	</PixelModal>
</template>

<style scoped>
.stress-dialog-body {
	display: flex;
	flex-direction: column;
	gap: 1.25rem;
}

.dialog-explainer {
	font-size: 0.9rem;
	color: var(--pixel-text-muted);
	line-height: 1.5;
}

.generate-trigger-bar {
	display: flex;
	justify-content: flex-start;
}

.cases-results {
	display: flex;
	flex-direction: column;
	gap: 0.75rem;
}

.cases-heading {
	font-family: var(--font-pixel);
	font-size: 12px;
	text-transform: uppercase;
	color: var(--pixel-text);
	margin: 0;
}

.cases-list {
	display: flex;
	flex-direction: column;
	gap: 0.75rem;
	max-height: 340px;
	overflow-y: auto;
}

.generated-item {
	background-color: var(--pixel-bg-alt);
}

.case-card-content {
	padding: 10px 12px;
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
}

.gen-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.pixel-checkbox-label {
	display: inline-flex;
	align-items: center;
	gap: 8px;
	cursor: pointer;
	font-family: var(--font-pixel);
	font-size: 11px;
	color: var(--pixel-text);
	user-select: none;
}

.pixel-checkbox {
	width: 16px;
	height: 16px;
	border: 2px solid var(--pixel-border);
	background-color: var(--pixel-surface);
	border-radius: 2px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.pixel-checkbox.checked {
	background-color: var(--pixel-btn-primary-bg);
	border-color: var(--pixel-btn-primary-border);
}

.gen-reason {
	font-size: 0.75rem;
	color: var(--pixel-text-dim);
	font-style: italic;
}

.gen-io {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 0.75rem;
	font-size: 0.8rem;
}

.io-col {
	display: flex;
	flex-direction: column;
	gap: 0.25rem;
}

.code-box {
	font-family: var(--font-mono);
	background-color: var(--pixel-surface);
	border: 1px solid var(--pixel-border);
	padding: 4px 6px;
	border-radius: 2px;
	white-space: pre-wrap;
	color: var(--pixel-text);
}

.modal-footer-actions {
	display: flex;
	align-items: center;
	justify-content: flex-end;
	gap: 8px;
	width: 100%;
}
</style>
