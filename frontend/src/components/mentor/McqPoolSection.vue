<script setup lang="ts">
import { ref, computed, watch } from 'vue'
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
	allowAdminEdit?: boolean
}>()

const emit = defineEmits<{
	(
		e: 'addMcq',
		payload: {
			prompt_text: string
			options: string[]
			correct_option_index: number
			explanation?: string
			difficulty: string
		},
	): void
	(
		e: 'updateMcq',
		mcqId: number,
		payload: {
			prompt_text: string
			options: string[]
			correct_option_index: number
			explanation?: string
			difficulty: string
		},
	): void
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
	},
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
			<div v-if="!isPublished || allowAdminEdit" class="header-action-group">
				<PixelButton
					size="small"
					color="secondary"
					icon="upload"
					@click="showImportDialog = true"
				>
					Import XLSX
				</PixelButton>
				<PixelButton size="small" color="primary" icon="plus" @click="showAddDialog = true">
					Add MCQ
				</PixelButton>
			</div>
		</div>

		<div v-if="mcqs.length > 0" class="cards-list">
			<PixelCard v-for="(mcq, index) in mcqs" :key="mcq.id" class="item-card">
				<PixelCardContent>
					<div class="card-inner">
						<div class="card-meta">
							<div class="meta-left">
								<span class="question-index-text">Q{{ index + 1 }}</span>
								<PixelBadge
									:color="
										mcq.difficulty === 'hard'
											? 'danger'
											: mcq.difficulty === 'medium'
												? 'warning'
												: 'success'
									"
									:text="mcq.difficulty.toUpperCase()"
								/>
								<PixelBadge
									:text="`+${mcq.difficulty === 'hard' ? 30 : mcq.difficulty === 'medium' ? 20 : 10} XP`"
									color="primary"
								/>
							</div>
							<div v-if="!isPublished || allowAdminEdit" class="meta-actions">
								<PixelButton
									color="secondary"
									size="small"
									icon="edit"
									aria-label="Edit question"
									@click="openEditDialog(mcq)"
								/>
								<PixelButton
									color="danger"
									size="small"
									icon="trash"
									aria-label="Delete question"
									@click="openDeleteDialog(mcq)"
								/>
							</div>
						</div>

						<p class="question-text">{{ formatEntities(mcq.prompt_text) }}</p>

						<div class="options-list">
							<div
								v-for="(opt, oIdx) in mcq.options"
								:key="oIdx"
								class="option-item"
								:class="{ correct: oIdx === mcq.correct_option_index }"
							>
								<span class="option-prefix"
									>{{ String.fromCharCode(65 + oIdx) }}.</span
								>

								<div class="option-content">
									{{ formatEntities(opt) }}
								</div>

								<div v-if="oIdx === mcq.correct_option_index" class="option-check">
									<PixelIcon name="check" :size="14" color="#34d399" />
								</div>
							</div>
						</div>

						<PixelAlert v-if="mcq.explanation" color="info" class="explanation-alert">
							{{ formatEntities(mcq.explanation) }}
						</PixelAlert>
					</div>
				</PixelCardContent>
			</PixelCard>
		</div>

		<PixelCard v-else class="empty-pool-card">
			<PixelCardContent class="empty-content">
				<PixelIcon name="edit" :size="48" class="empty-pool-icon" />
				<h3>No MCQs added yet</h3>
				<p>
					Author or bulk import at least 7 aptitude questions to fulfill the weekly set
					quota.
				</p>
			</PixelCardContent>
		</PixelCard>

		<!-- MODAL 1: CREATE MCQ -->
		<PixelModal
			v-model="showAddDialog"
			title="Author Aptitude MCQ"
			ok-text="Save MCQ"
			cancel-text="Cancel"
			:loading="isSubmitting"
			@ok="handleSaveAdd"
		>
			<form class="dialog-form" @submit.prevent="handleSaveAdd">
				<PixelTextarea
					v-model="newPrompt"
					label="Question Statement"
					placeholder="Enter the full question prompt..."
					:rows="3"
					required
				/>

				<PixelInput
					v-for="(_, i) in newOptions"
					:key="i"
					v-model="newOptions[i]"
					:label="`Option ${String.fromCharCode(65 + i)}`"
					:placeholder="`Choice ${String.fromCharCode(65 + i)} text`"
					required
				/>

				<PixelSelect
					v-model="newCorrectIndex"
					:options="correctOptionChoices"
					label="Correct Option"
					value-by="value"
					text-by="label"
					required
				/>

				<PixelSelect
					v-model="newDifficulty"
					:options="difficultyOptions"
					label="Question Difficulty"
					value-by="value"
					text-by="label"
				/>

				<PixelTextarea
					v-model="newExplanation"
					label="Explanation (Optional)"
					placeholder="Explain why the correct answer is right..."
					:rows="2"
				/>
			</form>
		</PixelModal>

		<!-- MODAL 2: EDIT MCQ -->
		<PixelModal
			v-model="showEditDialog"
			title="Edit Aptitude MCQ"
			ok-text="Update MCQ"
			cancel-text="Cancel"
			:loading="isSubmitting"
			@ok="handleSaveEdit"
		>
			<form class="dialog-form" @submit.prevent="handleSaveEdit">
				<PixelTextarea
					v-model="editPrompt"
					label="Question Statement"
					placeholder="Enter the full question prompt..."
					:rows="3"
					required
				/>

				<PixelInput
					v-for="(_, i) in editOptions"
					:key="i"
					v-model="editOptions[i]"
					:label="`Option ${String.fromCharCode(65 + i)}`"
					:placeholder="`Choice ${String.fromCharCode(65 + i)} text`"
					required
				/>

				<PixelSelect
					v-model="editCorrectIndex"
					:options="correctOptionChoices"
					label="Correct Option"
					value-by="value"
					text-by="label"
					required
				/>

				<PixelSelect
					v-model="editDifficulty"
					:options="difficultyOptions"
					label="Question Difficulty"
					value-by="value"
					text-by="label"
				/>

				<PixelTextarea
					v-model="editExplanation"
					label="Explanation (Optional)"
					placeholder="Explain why the correct answer is right..."
					:rows="2"
				/>
			</form>
		</PixelModal>

		<!-- MODAL 3: DELETE CONFIRMATION -->
		<PixelModal
			v-model="showDeleteDialog"
			title="Delete MCQ Question"
			ok-text="Delete"
			ok-color="danger"
			cancel-text="Cancel"
			@ok="handleConfirmDelete"
		>
			<p v-if="deleteTargetMcq">
				Are you sure you want to remove this MCQ?
				<br />
				<strong>"{{ deleteTargetMcq.prompt_text }}"</strong>
			</p>
		</PixelModal>

		<!-- MODAL 4: BULK IMPORT XLSX -->
		<PixelModal
			v-model="showImportDialog"
			title="Bulk Import MCQs from Spreadsheet"
			hide-default-actions
		>
			<div class="import-modal-content">
				<p class="import-instruction">
					Upload an <code>.xlsx</code> or <code>.csv</code> spreadsheet containing MCQs.
					AI will automatically parse the questions, options, correct answers, and
					explanations.
				</p>

				<PixelFileUpload
					v-model="uploadedImportFiles"
					file-types=".xlsx,.csv"
					type="single"
					@update:model-value="handleFileChange"
				/>

				<div class="modal-actions-row">
					<PixelButton
						color="secondary"
						:disabled="isImporting"
						@click="showImportDialog = false"
					>
						Cancel
					</PixelButton>
					<PixelButton
						color="primary"
						:loading="isImporting"
						:disabled="!selectedImportFile"
						icon="upload"
						@click="handleCommitImport"
					>
						Import with AI
					</PixelButton>
				</div>
			</div>
		</PixelModal>
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
	font-family: var(--font-pixel);
	font-size: 1.15rem;
	font-weight: 700;
	color: var(--pixel-text);
}

.cards-list {
	display: flex;
	flex-direction: column;
	gap: 1rem;
}

.item-card {
	border: 2px solid var(--pixel-border);
	box-shadow: 0 4px 0 0 var(--pixel-border-dark);
	background-color: var(--pixel-surface);
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
	gap: 0.75rem;
}

.question-index-text {
	font-family: var(--font-pixel);
	font-size: 13px;
	font-weight: 700;
	color: #fbbf24;
	letter-spacing: 0.04em;
}

.meta-actions {
	display: flex;
	align-items: center;
	gap: 0.25rem;
}

.question-text {
	font-size: 0.95rem;
	font-weight: 600;
	margin: 0;
	color: var(--pixel-text);
	line-height: 1.5;
}

.options-list {
	border: 1px solid var(--pixel-border);
	border-radius: 2px;
	overflow: hidden;
	background-color: var(--pixel-bg-alt);
}

.option-item {
	display: flex;
	align-items: center;
	gap: 0.65rem;
	padding: 0.5rem 0.75rem;
	border-bottom: 1px solid var(--pixel-border);
	transition: background-color 0.1s ease;
}

.option-item:last-child {
	border-bottom: none;
}

.option-item.correct {
	background-color: rgba(34, 197, 94, 0.12);
}

.option-prefix {
	font-family: var(--font-pixel);
	font-size: 12px;
	font-weight: 700;
	color: var(--pixel-text-muted);
	min-width: 18px;
	flex-shrink: 0;
}

.option-item.correct .option-prefix {
	color: #34d399;
}

.option-content {
	flex: 1;
	font-size: 0.88rem;
	color: var(--pixel-text);
	line-height: 1.4;
}

.option-check {
	display: flex;
	align-items: center;
	flex-shrink: 0;
}

.explanation-alert {
	margin-top: 0.25rem;
}

.empty-pool-card {
	border: 2px dashed var(--pixel-border);
	background-color: var(--pixel-surface);
}

.empty-content {
	padding: 3rem 2rem;
	text-align: center;
	color: var(--pixel-text-muted);
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
	color: var(--pixel-text-muted);
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
