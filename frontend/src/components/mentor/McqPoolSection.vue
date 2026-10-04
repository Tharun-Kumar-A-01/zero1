<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import XpStarBadge from '@/components/common/XpStarBadge.vue'
import type { MCQItem } from '@/types'

function formatEntities(str?: string): string {
	if (!str) return ''
	return str
		.replace(/&lt;/g, '<')
		.replace(/&gt;/g, '>')
		.replace(/&amp;/g, '&')
		.replace(/&quot;/g, '"')
		.replace(/&#39;/g, "'")
}

const props = defineProps<{
	mcqs: MCQItem[]
	isPublished: boolean
	isSubmitting: boolean
	isImporting?: boolean
}>()

const emit = defineEmits<{
	(e: 'addMcq', payload: {
		prompt_text: string
		options: string[]
		correct_option_index: number
		explanation?: string
		difficulty: string
	}): void
	(e: 'updateMcq', mcqId: number, payload: {
		prompt_text: string
		options: string[]
		correct_option_index: number
		explanation?: string
		difficulty: string
	}): void
	(e: 'deleteMcq', mcqId: number): void
	(e: 'importMcqs', file: File): void
}>()

// Add Dialog State
const showAddDialog = ref<boolean>(false)
const newPrompt = ref<string>('')
const newOptions = ref<string[]>(['', '', '', ''])
const newCorrectIndex = ref<number>(0)
const newExplanation = ref<string>('')
const newDifficulty = ref<string>('easy')

// Edit Dialog State
const showEditDialog = ref<boolean>(false)
const editMcqId = ref<number | null>(null)
const editPrompt = ref<string>('')
const editOptions = ref<string[]>(['', '', '', ''])
const editCorrectIndex = ref<number>(0)
const editExplanation = ref<string>('')
const editDifficulty = ref<string>('easy')

// Delete Dialog State
const showDeleteDialog = ref<boolean>(false)
const deleteTargetMcq = ref<MCQItem | null>(null)

// Import Dialog State
const showImportDialog = ref<boolean>(false)
const uploadedImportFiles = ref<File | File[] | undefined>(undefined)
const selectedImportFile = computed<File | null>(() => {
	const val = uploadedImportFiles.value
	if (!val) return null
	if (Array.isArray(val)) return val.length > 0 ? (val[0] ?? null) : null
	if (typeof val === 'object' && 'name' in val) return val as File
	return null
})

function handleFileChange(): void {
	if (document.activeElement instanceof HTMLElement) {
		document.activeElement.blur()
	}
}

watch(
	() => props.isImporting,
	(nowImporting, wasImporting) => {
		if (wasImporting && !nowImporting) {
			showImportDialog.value = false
			uploadedImportFiles.value = undefined
		}
	}
)

const difficultyOptions = [
	{ label: 'Easy (+10 XP)', value: 'easy' },
	{ label: 'Medium (+20 XP)', value: 'medium' },
	{ label: 'Hard (+30 XP)', value: 'hard' },
]

const correctOptionChoices = [
	{ label: 'Option A', value: 0 },
	{ label: 'Option B', value: 1 },
	{ label: 'Option C', value: 2 },
	{ label: 'Option D', value: 3 },
]

function resetAddForm(): void {
	newPrompt.value = ''
	newOptions.value = ['', '', '', '']
	newCorrectIndex.value = 0
	newExplanation.value = ''
	newDifficulty.value = 'easy'
}

function handleSaveAdd(): void {
	if (!newPrompt.value.trim()) return
	if (newOptions.value.some((o) => !o.trim())) return

	emit('addMcq', {
		prompt_text: newPrompt.value,
		options: [...newOptions.value],
		correct_option_index: newCorrectIndex.value,
		explanation: newExplanation.value.trim() || undefined,
		difficulty: newDifficulty.value,
	})

	showAddDialog.value = false
	resetAddForm()
}

function openEditDialog(mcq: MCQItem): void {
	editMcqId.value = mcq.id
	editPrompt.value = formatEntities(mcq.prompt_text)
	editOptions.value = mcq.options.map((o) => formatEntities(o))
	while (editOptions.value.length < 4) {
		editOptions.value.push('')
	}
	editCorrectIndex.value = mcq.correct_option_index
	editExplanation.value = formatEntities(mcq.explanation || '')
	editDifficulty.value = mcq.difficulty || 'medium'
	showEditDialog.value = true
}

function handleSaveEdit(): void {
	if (!editMcqId.value || !editPrompt.value.trim()) return
	if (editOptions.value.some((o) => !o.trim())) return

	emit('updateMcq', editMcqId.value, {
		prompt_text: editPrompt.value.trim(),
		options: [...editOptions.value],
		correct_option_index: editCorrectIndex.value,
		explanation: editExplanation.value.trim() || undefined,
		difficulty: editDifficulty.value,
	})

	showEditDialog.value = false
	editMcqId.value = null
}

function openDeleteDialog(mcq: MCQItem): void {
	deleteTargetMcq.value = mcq
	showDeleteDialog.value = true
}

function handleConfirmDelete(): void {
	if (deleteTargetMcq.value) {
		emit('deleteMcq', deleteTargetMcq.value.id)
	}
	showDeleteDialog.value = false
	deleteTargetMcq.value = null
}

function handleCommitImport(): void {
	if (selectedImportFile.value) {
		emit('importMcqs', selectedImportFile.value)
	}
}
</script>

<template>
	<div class="pool-container">
		<div class="pool-header">
			<h2 class="section-title">MCQ Questions</h2>
			<div v-if="!isPublished" class="header-action-group">
				<VaButton
					size="small"
					preset="secondary"
					icon="upload_file"
					@click="showImportDialog = true"
				>
					Import XLSX
				</VaButton>
				<VaButton
					size="small"
					icon="add"
					@click="showAddDialog = true"
				>
					Add MCQ
				</VaButton>
			</div>
		</div>

		<div v-if="mcqs.length > 0" class="cards-list">
			<VaCard
				v-for="(mcq, index) in mcqs"
				:key="mcq.id"
				class="item-card"
			>
				<VaCardContent>
					<div class="card-inner">
						<div class="card-meta">
							<div class="meta-left">
								<VaBadge color="backgroundElement" :text="`Q${index + 1}`" />
								<VaBadge
									:color="mcq.difficulty === 'hard' ? 'danger' : mcq.difficulty === 'medium' ? 'warning' : 'success'"
									:text="mcq.difficulty.toUpperCase()"
								/>
								<XpStarBadge
									:points="mcq.difficulty === 'hard' ? 30 : mcq.difficulty === 'medium' ? 20 : 10"
									size="small"
								/>
							</div>
							<div v-if="!isPublished" class="meta-actions">
								<VaButton
									preset="plain"
									icon="edit"
									size="small"
									aria-label="Edit question"
									@click="openEditDialog(mcq)"
								/>
								<VaButton
									preset="plain"
									icon="delete"
									color="danger"
									size="small"
									aria-label="Delete question"
									@click="openDeleteDialog(mcq)"
								/>
							</div>
						</div>

						<p class="question-text">{{ formatEntities(mcq.prompt_text) }}</p>

						<VaList class="options-list">
							<VaListItem
								v-for="(opt, oIdx) in mcq.options"
								:key="oIdx"
								class="option-item"
								:class="{ correct: oIdx === mcq.correct_option_index }"
							>
								<VaListItemSection avatar>
									<VaBadge
										:text="String.fromCharCode(65 + oIdx)"
										:color="oIdx === mcq.correct_option_index ? 'success' : 'backgroundElement'"
										:text-color="oIdx === mcq.correct_option_index ? 'textInverted' : undefined"
									/>
								</VaListItemSection>

								<VaListItemSection>
									<VaListItemLabel class="option-content">
										{{ formatEntities(opt) }}
									</VaListItemLabel>
								</VaListItemSection>

								<VaListItemSection icon v-if="oIdx === mcq.correct_option_index">
									<VaIcon name="check" color="success" />
								</VaListItemSection>
							</VaListItem>
						</VaList>

						<VaAlert v-if="mcq.explanation" color="info" border="left" class="explanation-alert">
							<template #icon>
								<VaIcon name="info" />
							</template>
							{{ formatEntities(mcq.explanation) }}
						</VaAlert>
					</div>
				</VaCardContent>
			</VaCard>
		</div>

		<VaCard v-else class="empty-pool-card">
			<VaCardContent class="empty-content">
				<VaIcon name="edit_note" size="48px" color="secondary" class="empty-pool-icon" />
				<h3>No MCQs added yet</h3>
				<p>Author or bulk import at least 7 aptitude questions to fulfill the weekly set quota.</p>
			</VaCardContent>
		</VaCard>

		<!-- MODAL 1: CREATE MCQ -->
		<VaModal
			v-model="showAddDialog"
			title="Author Aptitude MCQ"
			ok-text="Save MCQ"
			cancel-text="Cancel"
			:loading="isSubmitting"
			@ok="handleSaveAdd"
		>
			<VaForm class="dialog-form">
				<VaTextarea
					v-model="newPrompt"
					label="Question Statement"
					placeholder="Enter the full question prompt..."
					autosize
					:min-rows="3"
					required
				/>

				<VaInput
					v-for="(_, i) in newOptions"
					:key="i"
					v-model="newOptions[i]"
					:label="`Option ${String.fromCharCode(65 + i)}`"
					:placeholder="`Choice ${String.fromCharCode(65 + i)} text`"
					required
				/>

				<VaSelect
					v-model="newCorrectIndex"
					:options="correctOptionChoices"
					label="Correct Option"
					value-by="value"
					text-by="label"
					required
				/>

				<VaSelect
					v-model="newDifficulty"
					:options="difficultyOptions"
					label="Question Difficulty"
					value-by="value"
					text-by="label"
				/>

				<VaTextarea
					v-model="newExplanation"
					label="Explanation (Optional)"
					placeholder="Explain why the correct answer is right..."
					autosize
					:min-rows="2"
				/>
			</VaForm>
		</VaModal>

		<!-- MODAL 2: EDIT MCQ -->
		<VaModal
			v-model="showEditDialog"
			title="Edit Aptitude MCQ"
			ok-text="Update MCQ"
			cancel-text="Cancel"
			:loading="isSubmitting"
			@ok="handleSaveEdit"
		>
			<VaForm class="dialog-form">
				<VaTextarea
					v-model="editPrompt"
					label="Question Statement"
					placeholder="Enter the full question prompt..."
					autosize
					:min-rows="3"
					required
				/>

				<VaInput
					v-for="(_, i) in editOptions"
					:key="i"
					v-model="editOptions[i]"
					:label="`Option ${String.fromCharCode(65 + i)}`"
					:placeholder="`Choice ${String.fromCharCode(65 + i)} text`"
					required
				/>

				<VaSelect
					v-model="editCorrectIndex"
					:options="correctOptionChoices"
					label="Correct Option"
					value-by="value"
					text-by="label"
					required
				/>

				<VaSelect
					v-model="editDifficulty"
					:options="difficultyOptions"
					label="Question Difficulty"
					value-by="value"
					text-by="label"
				/>

				<VaTextarea
					v-model="editExplanation"
					label="Explanation (Optional)"
					placeholder="Explain why the correct answer is right..."
					autosize
					:min-rows="2"
				/>
			</VaForm>
		</VaModal>

		<!-- MODAL 3: DELETE CONFIRMATION -->
		<VaModal
			v-model="showDeleteDialog"
			title="Delete MCQ Question"
			ok-text="Delete"
			cancel-text="Cancel"
			ok-color="danger"
			@ok="handleConfirmDelete"
		>
			<p v-if="deleteTargetMcq">
				Are you sure you want to remove this MCQ?
				<br />
				<strong>"{{ deleteTargetMcq.prompt_text }}"</strong>
			</p>
		</VaModal>

		<!-- MODAL 4: BULK IMPORT XLSX -->
		<VaModal
			v-model="showImportDialog"
			title="Bulk Import MCQs from Spreadsheet"
			hide-default-actions
		>
			<div class="import-modal-content">
				<p class="import-instruction">
					Upload an <code>.xlsx</code> or <code>.csv</code> spreadsheet containing MCQs. AI will automatically parse the questions, options, correct answers, and explanations.
				</p>

				<VaFileUpload
					v-model="uploadedImportFiles"
					dropzone
					file-types=".xlsx,.csv"
					type="single"
					@update:model-value="handleFileChange"
				/>

				<div class="modal-actions-row">
					<VaButton
						preset="secondary"
						:disabled="isImporting"
						@click="showImportDialog = false"
					>
						Cancel
					</VaButton>
					<VaButton
						:loading="isImporting"
						:disabled="!selectedImportFile"
						icon="auto_awesome"
						@click="handleCommitImport"
					>
						Import with AI
					</VaButton>
				</div>
			</div>
		</VaModal>
	</div>
</template>

<style scoped>
.pool-container {
	display: flex;
	flex-direction: column;
	gap: 1.25rem;
}

.pool-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.header-action-group {
	display: flex;
	align-items: center;
	gap: 0.75rem;
}

.section-title {
	margin: 0;
	font-size: 1.25rem;
	font-weight: 700;
	color: var(--va-text-primary);
}

.cards-list {
	display: flex;
	flex-direction: column;
	gap: 1rem;
}

.item-card {
	border: 1px solid var(--va-background-border);
}

.card-inner {
	display: flex;
	flex-direction: column;
	gap: 0.75rem;
}

.card-meta {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.meta-left {
	display: flex;
	align-items: center;
	gap: 0.5rem;
}

.meta-actions {
	display: flex;
	align-items: center;
	gap: 0.25rem;
}

.question-text {
	font-size: 1rem;
	font-weight: 600;
	margin: 0;
	color: var(--va-text-primary);
	line-height: 1.5;
}

.options-list {
	border: 1px solid var(--va-background-border);
	border-radius: 4px;
	overflow: hidden;
}

.option-item {
	padding: 0.5rem 0.75rem;
	transition: background-color 0.15s ease;
}

.option-item.correct {
	background-color: rgba(61, 146, 9, 0.08);
}

.option-content {
	font-size: 0.9rem;
	color: var(--va-text-primary);
}

.explanation-alert {
	margin-top: 0.25rem;
}

.empty-pool-card {
	border: 2px dashed var(--va-background-border);
}

.empty-content {
	padding: 3rem 2rem;
	text-align: center;
	color: var(--va-text-secondary);
}

.empty-pool-icon {
	margin-bottom: 0.75rem;
}

.dialog-form {
	display: flex;
	flex-direction: column;
	gap: 1rem;
	padding: 0.5rem 0;
}

/* IMPORT MODAL */
.import-modal-content {
	display: flex;
	flex-direction: column;
	gap: 1rem;
	padding: 0.5rem 0;
}

.import-instruction {
	font-size: 0.88rem;
	color: var(--va-text-secondary);
	margin: 0;
	line-height: 1.5;
}

.modal-actions-row {
	display: flex;
	justify-content: flex-end;
	align-items: center;
	gap: 0.75rem;
	margin-top: 0.75rem;
}
</style>
