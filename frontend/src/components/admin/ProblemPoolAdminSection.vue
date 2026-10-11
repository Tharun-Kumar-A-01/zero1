<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import type { QuestionSetItem, MCQItem, CodingQuestionItem } from '@/types'
import { usePixelToast } from '@/components/pixel/usePixelToast'
import PixelButton from '@/components/pixel/PixelButton.vue'
import PixelCard from '@/components/pixel/PixelCard.vue'
import PixelCardContent from '@/components/pixel/PixelCardContent.vue'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'
import PixelModal from '@/components/pixel/PixelModal.vue'
import PixelInput from '@/components/pixel/PixelInput.vue'
import PixelSelect from '@/components/pixel/PixelSelect.vue'
import McqPoolSection from '@/components/mentor/McqPoolSection.vue'
import CodingPoolSection from '@/components/mentor/CodingPoolSection.vue'
import AiStressTestDialog from '@/components/mentor/AiStressTestDialog.vue'

interface QuestionSetDetail extends QuestionSetItem {
	mcqs: MCQItem[]
	coding_questions: CodingQuestionItem[]
}

const { init: notify } = usePixelToast()

const questionSets = ref<QuestionSetItem[]>([])
const selectedSetId = ref<number | null>(null)
const selectedSet = ref<QuestionSetDetail | null>(null)
const isLoading = ref<boolean>(false)
const isSubmitting = ref<boolean>(false)

// Active Problem Sub-tab
const activeProblemTab = ref<'mcq' | 'coding'>('mcq')

// AI Test Case Gen State
const showAiModal = ref<boolean>(false)
const aiTargetProblem = ref<CodingQuestionItem | null>(null)
const isGeneratingAiTests = ref<boolean>(false)
const generatedAiCases = ref<Array<{ input: string; expected_output: string; rationale?: string }>>(
	[],
)

// Create Question Set Modal State
const showCreateSetModal = ref<boolean>(false)
const newSetStatus = ref<string>('published')
const newSetWeekDate = ref<string>(new Date().toISOString().split('T')[0] ?? '')

// Delete Question Set State
const showDeleteSetModal = ref<boolean>(false)

const statusOptions = [
	{ label: 'Publish Immediately (Live for Students)', value: 'published' },
	{ label: 'Save as Draft', value: 'draft' },
]

async function fetchQuestionSets(): Promise<void> {
	isLoading.value = true
	try {
		const res = await api.get<QuestionSetItem[]>('/admin/question-sets')
		if (res.success && res.data) {
			questionSets.value = res.data
			if (!selectedSetId.value && questionSets.value.length > 0) {
				const publishedSet = questionSets.value.find((s) => s.status === 'published')
				selectedSetId.value = publishedSet
					? publishedSet.id
					: (questionSets.value[0]?.id ?? null)
			}
			if (selectedSetId.value) {
				await loadSetDetails(selectedSetId.value)
			}
		}
	} catch {
		notify({ color: 'danger', message: 'Failed to fetch question sets.' })
	} finally {
		isLoading.value = false
	}
}

async function loadSetDetails(setId: number): Promise<void> {
	try {
		const res = await api.get<QuestionSetDetail>(`/admin/question-sets/${setId}`)
		if (res.success && res.data) {
			selectedSet.value = res.data
			selectedSetId.value = setId
		}
	} catch {
		notify({ color: 'danger', message: 'Failed to load question set details.' })
	}
}

async function handleSelectSet(id: number): Promise<void> {
	if (selectedSetId.value === id) return
	await loadSetDetails(id)
}

async function handlePublishSet(): Promise<void> {
	if (!selectedSetId.value) return
	isSubmitting.value = true
	try {
		const res = await api.post<QuestionSetDetail>(
			`/admin/question-sets/${selectedSetId.value}/publish`,
		)
		if (res.success && res.data) {
			notify({
				color: 'success',
				message: 'Question set is now PUBLISHED and live for students.',
			})
			await fetchQuestionSets()
		}
	} catch {
		notify({ color: 'danger', message: 'Failed to publish question set.' })
	} finally {
		isSubmitting.value = false
	}
}

async function handleUnpublishSet(): Promise<void> {
	if (!selectedSetId.value) return
	isSubmitting.value = true
	try {
		const res = await api.post<QuestionSetDetail>(
			`/admin/question-sets/${selectedSetId.value}/unpublish`,
		)
		if (res.success && res.data) {
			notify({ color: 'warning', message: 'Question set moved to DRAFT.' })
			await fetchQuestionSets()
		}
	} catch {
		notify({ color: 'danger', message: 'Failed to unpublish question set.' })
	} finally {
		isSubmitting.value = false
	}
}

async function handleCreateSet(): Promise<void> {
	isSubmitting.value = true
	try {
		const res = await api.post<{ id: number }>('/admin/question-sets', {
			status: newSetStatus.value,
			week_start_date: newSetWeekDate.value || undefined,
		})
		if (res.success && res.data) {
			notify({ color: 'success', message: 'New question set created.' })
			showCreateSetModal.value = false
			selectedSetId.value = res.data.id
			await fetchQuestionSets()
		}
	} catch {
		notify({ color: 'danger', message: 'Failed to create question set.' })
	} finally {
		isSubmitting.value = false
	}
}

async function handleConfirmDeleteSet(): Promise<void> {
	if (!selectedSetId.value) return
	isSubmitting.value = true
	try {
		const res = await api.delete(`/admin/question-sets/${selectedSetId.value}`)
		if (res.success) {
			notify({ color: 'success', message: 'Question set deleted.' })
			showDeleteSetModal.value = false
			selectedSetId.value = null
			selectedSet.value = null
			await fetchQuestionSets()
		}
	} catch {
		notify({ color: 'danger', message: 'Failed to delete question set.' })
	} finally {
		isSubmitting.value = false
	}
}

// MCQ Actions
async function handleAddMcq(payload: {
	prompt_text: string
	options: string[]
	correct_option_index: number
	explanation?: string
	difficulty: string
}): Promise<void> {
	if (!selectedSetId.value) return
	isSubmitting.value = true
	try {
		const res = await api.post('/mentor/questions/mcq', {
			...payload,
			question_set_id: selectedSetId.value,
		})
		if (res.success) {
			notify({ color: 'success', message: 'MCQ added to question pool.' })
			await loadSetDetails(selectedSetId.value)
		}
	} catch {
		notify({ color: 'danger', message: 'Failed to add MCQ.' })
	} finally {
		isSubmitting.value = false
	}
}

async function handleUpdateMcq(
	mcqId: number,
	payload: {
		prompt_text: string
		options: string[]
		correct_option_index: number
		explanation?: string
		difficulty: string
	},
): Promise<void> {
	if (!selectedSetId.value) return
	isSubmitting.value = true
	try {
		const res = await api.put(`/mentor/questions/mcq/${mcqId}`, payload)
		if (res.success) {
			notify({ color: 'success', message: 'MCQ updated.' })
			await loadSetDetails(selectedSetId.value)
		}
	} catch {
		notify({ color: 'danger', message: 'Failed to update MCQ.' })
	} finally {
		isSubmitting.value = false
	}
}

async function handleDeleteMcq(mcqId: number): Promise<void> {
	if (!selectedSetId.value) return
	isSubmitting.value = true
	try {
		const res = await api.delete(`/mentor/questions/mcq/${mcqId}`)
		if (res.success) {
			notify({ color: 'success', message: 'MCQ removed from pool.' })
			await loadSetDetails(selectedSetId.value)
		}
	} catch {
		notify({ color: 'danger', message: 'Failed to delete MCQ.' })
	} finally {
		isSubmitting.value = false
	}
}

async function handleImportMcqs(file: File): Promise<void> {
	if (!selectedSetId.value) return
	isSubmitting.value = true
	try {
		const formData = new FormData()
		formData.append('file', file)
		formData.append('question_set_id', String(selectedSetId.value))
		const res = await api.upload('/mentor/questions/import-mcq-sheet', formData)
		if (res.success) {
			notify({ color: 'success', message: 'MCQ spreadsheet imported.' })
			await loadSetDetails(selectedSetId.value)
		}
	} catch {
		notify({ color: 'danger', message: 'Failed to import MCQs.' })
	} finally {
		isSubmitting.value = false
	}
}

// Coding Problem Actions
async function handleAddCoding(payload: any): Promise<void> {
	if (!selectedSetId.value) return
	isSubmitting.value = true
	try {
		const res = await api.post('/mentor/questions/coding', {
			...payload,
			question_set_id: selectedSetId.value,
		})
		if (res.success) {
			notify({ color: 'success', message: 'Coding problem added to pool.' })
			await loadSetDetails(selectedSetId.value)
		}
	} catch {
		notify({ color: 'danger', message: 'Failed to add coding problem.' })
	} finally {
		isSubmitting.value = false
	}
}

async function handleUpdateCoding(codingQId: number, payload: any): Promise<void> {
	if (!selectedSetId.value) return
	isSubmitting.value = true
	try {
		const res = await api.put(`/mentor/questions/coding/${codingQId}`, payload)
		if (res.success) {
			notify({ color: 'success', message: 'Coding problem updated.' })
			await loadSetDetails(selectedSetId.value)
		}
	} catch {
		notify({ color: 'danger', message: 'Failed to update coding problem.' })
	} finally {
		isSubmitting.value = false
	}
}

async function handleDeleteCoding(codingQId: number): Promise<void> {
	if (!selectedSetId.value) return
	isSubmitting.value = true
	try {
		const res = await api.delete(`/mentor/questions/coding/${codingQId}`)
		if (res.success) {
			notify({ color: 'success', message: 'Coding challenge removed.' })
			await loadSetDetails(selectedSetId.value)
		}
	} catch {
		notify({ color: 'danger', message: 'Failed to delete coding problem.' })
	} finally {
		isSubmitting.value = false
	}
}

async function handleImportCoding(file: File): Promise<void> {
	if (!selectedSetId.value) return
	isSubmitting.value = true
	try {
		const formData = new FormData()
		formData.append('file', file)
		formData.append('question_set_id', String(selectedSetId.value))
		const res = await api.upload('/mentor/questions/import-coding-sheet', formData)
		if (res.success) {
			notify({ color: 'success', message: 'Coding spreadsheet imported.' })
			await loadSetDetails(selectedSetId.value)
		}
	} catch {
		notify({ color: 'danger', message: 'Failed to import coding challenges.' })
	} finally {
		isSubmitting.value = false
	}
}

function handleOpenAiGen(problem: CodingQuestionItem): void {
	aiTargetProblem.value = problem
	generatedAiCases.value = []
	showAiModal.value = true
}

async function triggerAiGeneration(): Promise<void> {
	if (!aiTargetProblem.value) return
	isGeneratingAiTests.value = true
	try {
		const res = await api.post<{
			test_cases: Array<{ input: string; expected_output: string; rationale?: string }>
		}>(`/mentor/coding/${aiTargetProblem.value.id}/generate-ai-tests`)
		if (res.success && res.data) {
			generatedAiCases.value = res.data.test_cases
			notify({
				color: 'success',
				message: `Synthesized ${res.data.test_cases.length} AI edge cases.`,
			})
		} else {
			notify({ color: 'danger', message: res.error?.message || 'AI test generation failed.' })
		}
	} catch (err: unknown) {
		notify({
			color: 'danger',
			message: err instanceof Error ? err.message : 'Generation network error',
		})
	} finally {
		isGeneratingAiTests.value = false
	}
}

async function handleAcceptAiCases(
	cases: Array<{ input: string; expected_output: string }>,
): Promise<void> {
	if (!aiTargetProblem.value) return
	try {
		const res = await api.post(`/mentor/coding/${aiTargetProblem.value.id}/append-test-cases`, {
			test_cases: cases,
		})
		if (res.success) {
			showAiModal.value = false
			notify({
				color: 'success',
				message: `Appended ${cases.length} AI cases to test suite.`,
			})
			if (selectedSetId.value) {
				await loadSetDetails(selectedSetId.value)
			}
		}
	} catch (err: unknown) {
		notify({
			color: 'danger',
			message: err instanceof Error ? err.message : 'Failed to save test cases',
		})
	}
}

onMounted(async () => {
	await fetchQuestionSets()
})
</script>

<template>
	<div class="problem-admin-container">
		<!-- Header Controls -->
		<div class="problem-admin-header">
			<div class="header-info">
				<h2 class="section-title">Practice Problem Sets & Publishing</h2>
			</div>

			<div class="header-actions">
				<PixelButton
					color="secondary"
					size="small"
					icon="refresh"
					@click="fetchQuestionSets"
				>
					Refresh
				</PixelButton>
				<PixelButton
					color="primary"
					size="small"
					icon="plus"
					@click="showCreateSetModal = true"
				>
					New Question Set
				</PixelButton>
			</div>
		</div>

		<!-- Question Sets Row Selector -->
		<div class="sets-selector-strip">
			<div
				v-for="qs in questionSets"
				:key="qs.id"
				class="set-tile"
				:class="{
					'set-tile--active': qs.id === selectedSetId,
					'set-tile--published': qs.status === 'published',
				}"
				@click="handleSelectSet(qs.id)"
			>
				<div class="tile-top-row">
					<span class="tile-id">SET #{{ qs.id }}</span>
					<PixelBadge
						:text="qs.status.toUpperCase()"
						:color="
							qs.status === 'published'
								? 'success'
								: qs.status === 'draft'
									? 'warning'
									: 'secondary'
						"
					/>
				</div>
				<div class="tile-author">{{ qs.mentor_name || 'Admin Pool' }}</div>
				<div class="tile-counts">
					<span>{{ qs.mcq_count }} MCQs</span>
					<span class="dot-sep">•</span>
					<span>{{ qs.coding_count }} Coding</span>
				</div>
			</div>
		</div>

		<!-- Selected Question Set Control Card -->
		<PixelCard v-if="selectedSet" class="set-meta-card">
			<PixelCardContent>
				<div class="meta-card-inner">
					<div class="set-main-info">
						<div class="set-title-row">
							<h3 class="set-heading">Question Set #{{ selectedSet.id }}</h3>
							<PixelBadge
								:text="
									selectedSet.status === 'published'
										? 'LIVE FOR STUDENTS'
										: selectedSet.status.toUpperCase()
								"
								:color="selectedSet.status === 'published' ? 'success' : 'warning'"
							/>
						</div>
						<p class="set-author-text">
							Curator: <strong>{{ selectedSet.mentor_name }}</strong>
							<span v-if="selectedSet.week_start_date">
								| Rotation Week: {{ selectedSet.week_start_date }}</span
							>
						</p>
					</div>

					<div class="set-actions-row">
						<PixelButton
							v-if="selectedSet.status !== 'published'"
							color="success"
							size="medium"
							icon="check"
							:loading="isSubmitting"
							@click="handlePublishSet"
						>
							Publish to Live
						</PixelButton>

						<PixelButton
							v-else
							color="secondary"
							size="medium"
							icon="close"
							:loading="isSubmitting"
							@click="handleUnpublishSet"
						>
							Unpublish (Draft)
						</PixelButton>

						<PixelButton
							color="danger"
							size="medium"
							icon="trash"
							:disabled="questionSets.length <= 1"
							@click="showDeleteSetModal = true"
						>
							Delete Set
						</PixelButton>
					</div>
				</div>
			</PixelCardContent>
		</PixelCard>

		<!-- Sub-Tabs: MCQ Questions vs Coding Problems -->
		<div v-if="selectedSet" class="problem-type-tabs">
			<button
				type="button"
				class="type-tab-btn"
				:class="{ active: activeProblemTab === 'mcq' }"
				@click="activeProblemTab = 'mcq'"
			>
				<span>Aptitude MCQs ({{ selectedSet.mcqs?.length || 0 }})</span>
			</button>

			<button
				type="button"
				class="type-tab-btn"
				:class="{ active: activeProblemTab === 'coding' }"
				@click="activeProblemTab = 'coding'"
			>
				<span>Coding Challenges ({{ selectedSet.coding_questions?.length || 0 }})</span>
			</button>
		</div>

		<!-- MCQ Pool View -->
		<div v-if="selectedSet && activeProblemTab === 'mcq'" class="tab-panel">
			<McqPoolSection
				:mcqs="selectedSet.mcqs || []"
				:is-published="selectedSet.status === 'published'"
				:allow-admin-edit="true"
				:is-submitting="isSubmitting"
				@add-mcq="handleAddMcq"
				@update-mcq="handleUpdateMcq"
				@delete-mcq="handleDeleteMcq"
				@import-mcqs="handleImportMcqs"
			/>
		</div>

		<!-- Coding Pool View -->
		<div v-if="selectedSet && activeProblemTab === 'coding'" class="tab-panel">
			<CodingPoolSection
				:coding-questions="selectedSet.coding_questions || []"
				:is-published="selectedSet.status === 'published'"
				:allow-admin-edit="true"
				:is-submitting="isSubmitting"
				@add-coding="handleAddCoding"
				@update-coding="handleUpdateCoding"
				@delete-coding="handleDeleteCoding"
				@import-coding="handleImportCoding"
				@open-ai-gen="handleOpenAiGen"
			/>
		</div>

		<!-- AI Stress Test Dialog -->
		<AiStressTestDialog
			v-model:visible="showAiModal"
			:question="aiTargetProblem"
			:is-generating="isGeneratingAiTests"
			:generated-cases="generatedAiCases"
			@generate="triggerAiGeneration"
			@accept="handleAcceptAiCases"
		/>

		<!-- Create Question Set Modal -->
		<PixelModal
			v-model="showCreateSetModal"
			title="Create Practice Question Set"
			ok-text="Create Set"
			cancel-text="Cancel"
			:loading="isSubmitting"
			@ok="handleCreateSet"
		>
			<div class="modal-form">
				<PixelSelect
					v-model="newSetStatus"
					label="Initial Status"
					:options="statusOptions"
					value-by="value"
					text-by="label"
				/>

				<PixelInput v-model="newSetWeekDate" type="date" label="Week Start Date" />
			</div>
		</PixelModal>

		<!-- Delete Set Confirmation Modal -->
		<PixelModal
			v-model="showDeleteSetModal"
			title="Delete Question Set"
			ok-text="Delete Set"
			ok-color="danger"
			cancel-text="Cancel"
			:loading="isSubmitting"
			@ok="handleConfirmDeleteSet"
		>
			<div class="delete-confirm-content">
				<p>
					Are you sure you want to delete
					<strong>Question Set #{{ selectedSetId }}</strong
					>?
				</p>
				<p class="delete-warning">
					All child MCQs and coding challenges in this set will be permanently removed.
				</p>
			</div>
		</PixelModal>
	</div>
</template>

<style scoped>
.problem-admin-container {
	display: flex;
	flex-direction: column;
	gap: 1.25rem;
}

.problem-admin-header {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	flex-wrap: wrap;
	gap: 1rem;
}

.section-title {
	font-family: var(--font-pixel);
	font-size: 1.25rem;
	letter-spacing: -0.01em;
	color: var(--pixel-text);
	margin: 0 0 0.35rem 0;
}

.section-desc {
	font-size: 0.9rem;
	color: var(--pixel-text-muted);
	margin: 0;
}

.header-actions {
	display: flex;
	align-items: center;
	gap: 0.75rem;
}

.sets-selector-strip {
	display: flex;
	align-items: stretch;
	gap: 0.75rem;
	overflow-x: auto;
	padding-bottom: 0.5rem;
}

.set-tile {
	min-width: 175px;
	background: var(--pixel-surface-alt);
	border: 2px solid var(--pixel-border);
	box-shadow: 0 3px 0 0 var(--pixel-border-dark);
	border-radius: 3px;
	padding: 0.75rem 1rem;
	cursor: pointer;
	display: flex;
	flex-direction: column;
	gap: 0.4rem;
	transition: all 0.1s ease;
}

.set-tile:hover {
	background: var(--pixel-surface-raised);
	border-color: var(--pixel-border-bright);
}

.set-tile--active {
	border-color: var(--pixel-btn-primary-bg);
	box-shadow: 0 1px 0 0 var(--pixel-border-dark);
	transform: translateY(2px);
	background: var(--pixel-surface);
}

.tile-top-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.tile-id {
	font-family: var(--font-pixel);
	font-size: 0.85rem;
	color: var(--pixel-text);
}

.tile-author {
	font-size: 0.85rem;
	color: var(--pixel-text-dim);
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.tile-counts {
	display: flex;
	align-items: center;
	gap: 0.4rem;
	font-size: 0.8rem;
	color: var(--pixel-text-muted);
	font-family: var(--font-pixel);
}

.dot-sep {
	opacity: 0.5;
}

.set-meta-card {
	border-left: 4px solid var(--pixel-btn-primary-bg);
}

.meta-card-inner {
	display: flex;
	align-items: center;
	justify-content: space-between;
	flex-wrap: wrap;
	gap: 1.25rem;
}

.set-title-row {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	margin-bottom: 0.25rem;
}

.set-heading {
	font-family: var(--font-pixel);
	font-size: 1.15rem;
	margin: 0;
	color: var(--pixel-text);
}

.set-author-text {
	font-size: 0.85rem;
	color: var(--pixel-text-muted);
	margin: 0;
}

.set-actions-row {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	flex-wrap: wrap;
}

.problem-type-tabs {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	border-bottom: 2px solid var(--pixel-border);
	padding-bottom: 0.5rem;
}

.type-tab-btn {
	background: var(--pixel-surface-alt);
	color: var(--pixel-text-muted);
	border: 2px solid var(--pixel-border);
	box-shadow: 0 2px 0 0 var(--pixel-border-dark);
	border-radius: 2px;
	padding: 0.5rem 1rem;
	font-family: var(--font-pixel);
	font-size: 0.85rem;
	text-transform: uppercase;
	cursor: pointer;
	transition: all 0.1s ease;
}

.type-tab-btn:hover {
	background: var(--pixel-surface-raised);
	color: var(--pixel-text);
}

.type-tab-btn.active {
	background: var(--pixel-btn-primary-bg);
	border-color: var(--pixel-btn-primary-border);
	color: #fff;
}

.modal-form {
	display: flex;
	flex-direction: column;
	gap: 1rem;
}

.delete-confirm-content {
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
}

.delete-warning {
	font-size: 0.85rem;
	color: var(--pixel-btn-danger-bg);
}
</style>
