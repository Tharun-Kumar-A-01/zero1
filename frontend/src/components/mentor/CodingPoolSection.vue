<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { CodingQuestionItem } from '@/types'
import RichTextEditor from '@/components/common/RichTextEditor.vue'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import XpStarBadge from '@/components/common/XpStarBadge.vue'
import api from '@/services/api'
import { useToast } from 'vuestic-ui'
import { generateBoilerplateTemplates } from '@/utils/boilerplate'

const props = defineProps<{
	codingQuestions: CodingQuestionItem[]
	isPublished: boolean
	isSubmitting: boolean
	isImporting?: boolean
}>()

const emit = defineEmits<{
	(e: 'addCoding', payload: {
		title: string
		word_problem_text: string
		constraints_text: string
		difficulty: string
		function_name?: string
		parameter_definitions?: Array<{ name: string; type: string }>
		return_type?: string
		starter_templates?: Record<string, string>
		sample_test_cases: Array<{ input: string; expected_output: string }>
		hidden_test_cases: Array<{ input: string; expected_output: string }>
	}): void
	(e: 'updateCoding', codingId: number, payload: {
		title: string
		word_problem_text: string
		constraints_text: string
		difficulty: string
		function_name?: string
		parameter_definitions?: Array<{ name: string; type: string }>
		return_type?: string
		starter_templates?: Record<string, string>
		sample_test_cases: Array<{ input: string; expected_output: string }>
		hidden_test_cases: Array<{ input: string; expected_output: string }>
	}): void
	(e: 'deleteCoding', codingId: number): void
	(e: 'openAiGen', question: CodingQuestionItem): void
	(e: 'importCoding', file: File): void
}>()

const { init: notify } = useToast()

// Helpers for client-side entity decoding & default test suites
function formatConstraints(str?: string): string {
	if (!str) return ''
	return str
		.replace(/&lt;/g, '<')
		.replace(/&gt;/g, '>')
		.replace(/&amp;/g, '&')
		.replace(/&quot;/g, '"')
		.replace(/&#39;/g, "'")
}

function getDefaultSampleCases(): Array<{ input: string; expected_output: string }> {
	return [
		{ input: '5\n1 2 3 4 5', expected_output: '15' },
		{ input: '3\n-1 -2 -3', expected_output: '-6' },
		{ input: '1\n42', expected_output: '42' },
	]
}

function getDefaultHiddenCases(): Array<{ input: string; expected_output: string }> {
	return [
		{ input: '4\n0 0 0 0', expected_output: '0' },
		{ input: '2\n100000 200000', expected_output: '300000' },
		{ input: '1\n0', expected_output: '0' },
		{ input: '3\n10 20 30', expected_output: '60' },
		{ input: '2\n-5 5', expected_output: '0' },
		{ input: '5\n-10 -20 -30 -40 -50', expected_output: '-150' },
		{ input: '4\n100 200 300 400', expected_output: '1000' },
		{ input: '1\n-100', expected_output: '-100' },
		{ input: '2\n1 1', expected_output: '2' },
		{ input: '6\n-2 4 -6 8 -10 12', expected_output: '6' },
	]
}

function getTestCaseCount(codeQ: CodingQuestionItem): number {
	const samples = codeQ.sample_test_cases?.length ?? 0
	const hiddens = codeQ.hidden_test_cases?.length ?? 0
	if (samples > 0 || hiddens > 0) {
		return samples + hiddens
	}
	if (codeQ.all_test_cases && codeQ.all_test_cases.length > 0) {
		return codeQ.all_test_cases.length
	}
	return 13
}

// Add Problem Dialog State
const showAddDialog = ref<boolean>(false)
const newTitle = ref<string>('')
const newProblem = ref<string>('')
const newConstraints = ref<string>('1 <= N <= 10^5\nAll values are within 32-bit signed integer limits.')
const newDifficulty = ref<string>('medium')
const newFunctionName = ref<string>('solve')
const newParameterDefs = ref<Array<{ name: string; type: string }>>([
	{ name: 'nums', type: 'int[]' },
])
const newReturnType = ref<string>('int')
const isGeneratingInlineAi = ref<boolean>(false)

const newSampleCases = ref<Array<{ input: string; expected_output: string }>>(getDefaultSampleCases())
const newHiddenCases = ref<Array<{ input: string; expected_output: string }>>(getDefaultHiddenCases())

// Edit Problem Dialog State
const showEditDialog = ref<boolean>(false)
const editCodingId = ref<number | null>(null)
const editTitle = ref<string>('')
const editProblem = ref<string>('')
const editConstraints = ref<string>('')
const editDifficulty = ref<string>('medium')
const editFunctionName = ref<string>('solve')
const editParameterDefs = ref<Array<{ name: string; type: string }>>([])
const editReturnType = ref<string>('int')
const editSampleCases = ref<Array<{ input: string; expected_output: string }>>([])
const editHiddenCases = ref<Array<{ input: string; expected_output: string }>>([])

// Delete Dialog State
const showDeleteDialog = ref<boolean>(false)
const deleteTargetCoding = ref<CodingQuestionItem | null>(null)

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
	{ label: 'Easy (+15 XP)', value: 'easy' },
	{ label: 'Medium (+30 XP)', value: 'medium' },
	{ label: 'Hard (+50 XP)', value: 'hard' },
]

function resetAddForm(): void {
	newTitle.value = ''
	newProblem.value = ''
	newConstraints.value = '1 <= N <= 10^5\nAll values are within 32-bit signed integer limits.'
	newDifficulty.value = 'medium'
	newFunctionName.value = 'solve'
	newParameterDefs.value = [{ name: 'nums', type: 'int[]' }]
	newReturnType.value = 'int'
	newSampleCases.value = getDefaultSampleCases()
	newHiddenCases.value = getDefaultHiddenCases()
}

function addParameterDef(isEdit: boolean): void {
	if (isEdit) {
		editParameterDefs.value.push({ name: `arg${editParameterDefs.value.length + 1}`, type: 'int' })
	} else {
		newParameterDefs.value.push({ name: `arg${newParameterDefs.value.length + 1}`, type: 'int' })
	}
}

function removeParameterDef(isEdit: boolean, index: number): void {
	if (isEdit) {
		if (editParameterDefs.value.length > 1) {
			editParameterDefs.value.splice(index, 1)
		}
	} else {
		if (newParameterDefs.value.length > 1) {
			newParameterDefs.value.splice(index, 1)
		}
	}
}

function handleSaveAdd(): void {
	if (!newTitle.value.trim() || !newProblem.value.trim()) {
		notify({ color: 'warning', message: 'Title and problem statement are required.' })
		return
	}

	for (let i = 0; i < newSampleCases.value.length; i++) {
		const tc = newSampleCases.value[i]!
		if (!tc.input.trim() || !tc.expected_output.trim()) {
			notify({ color: 'danger', message: `Sample Case ${i + 1} input and expected output cannot be empty.` })
			return
		}
	}

	for (let i = 0; i < newHiddenCases.value.length; i++) {
		const tc = newHiddenCases.value[i]!
		if (!tc.input.trim() || !tc.expected_output.trim()) {
			notify({ color: 'danger', message: `Hidden Case ${i + 1} input and expected output cannot be empty.` })
			return
		}
	}

	const templates = generateBoilerplateTemplates(
		newFunctionName.value,
		newParameterDefs.value,
		newReturnType.value
	)

	emit('addCoding', {
		title: newTitle.value.trim(),
		word_problem_text: newProblem.value.trim(),
		constraints_text: newConstraints.value.trim(),
		difficulty: newDifficulty.value,
		function_name: newFunctionName.value.trim() || 'solve',
		parameter_definitions: newParameterDefs.value.filter((p) => p.name.trim()),
		return_type: newReturnType.value.trim() || 'int',
		starter_templates: templates,
		sample_test_cases: newSampleCases.value.map((tc) => ({
			input: tc.input.trim(),
			expected_output: tc.expected_output.trim(),
		})),
		hidden_test_cases: newHiddenCases.value.map((tc) => ({
			input: tc.input.trim(),
			expected_output: tc.expected_output.trim(),
		})),
	})

	showAddDialog.value = false
	resetAddForm()
}

function openEditDialog(codeQ: CodingQuestionItem): void {
	editCodingId.value = codeQ.id
	editTitle.value = codeQ.title
	editProblem.value = codeQ.word_problem_text
	editConstraints.value = formatConstraints(codeQ.constraints_text || '')
	editDifficulty.value = codeQ.difficulty || 'medium'
	editFunctionName.value = codeQ.function_name || 'solve'
	editParameterDefs.value =
		codeQ.parameter_definitions && codeQ.parameter_definitions.length > 0
			? JSON.parse(JSON.stringify(codeQ.parameter_definitions))
			: [{ name: 'nums', type: 'int[]' }]
	editReturnType.value = codeQ.return_type || 'int'

	const samples = (codeQ.sample_test_cases || []).map((tc) => ({
		input: tc.input_data,
		expected_output: tc.expected_output,
	}))
	const hiddens = (codeQ.hidden_test_cases || []).map((tc) => ({
		input: tc.input_data,
		expected_output: tc.expected_output,
	}))

	editSampleCases.value = samples.length > 0 ? samples : getDefaultSampleCases()
	editHiddenCases.value = hiddens.length > 0 ? hiddens : getDefaultHiddenCases()
	showEditDialog.value = true
}

function handleSaveEdit(): void {
	if (!editCodingId.value || !editTitle.value.trim() || !editProblem.value.trim()) {
		notify({ color: 'warning', message: 'Title and problem statement are required.' })
		return
	}

	for (let i = 0; i < editSampleCases.value.length; i++) {
		const tc = editSampleCases.value[i]!
		if (!tc.input.trim() || !tc.expected_output.trim()) {
			notify({ color: 'danger', message: `Sample Case ${i + 1} input and expected output cannot be empty.` })
			return
		}
	}

	for (let i = 0; i < editHiddenCases.value.length; i++) {
		const tc = editHiddenCases.value[i]!
		if (!tc.input.trim() || !tc.expected_output.trim()) {
			notify({ color: 'danger', message: `Hidden Case ${i + 1} input and expected output cannot be empty.` })
			return
		}
	}

	const templates = generateBoilerplateTemplates(
		editFunctionName.value,
		editParameterDefs.value,
		editReturnType.value
	)

	emit('updateCoding', editCodingId.value, {
		title: editTitle.value.trim(),
		word_problem_text: editProblem.value.trim(),
		constraints_text: editConstraints.value.trim(),
		difficulty: editDifficulty.value,
		function_name: editFunctionName.value.trim() || 'solve',
		parameter_definitions: editParameterDefs.value.filter((p) => p.name.trim()),
		return_type: editReturnType.value.trim() || 'int',
		starter_templates: templates,
		sample_test_cases: editSampleCases.value.map((tc) => ({
			input: tc.input.trim(),
			expected_output: tc.expected_output.trim(),
		})),
		hidden_test_cases: editHiddenCases.value.map((tc) => ({
			input: tc.input.trim(),
			expected_output: tc.expected_output.trim(),
		})),
	})

	showEditDialog.value = false
	editCodingId.value = null
}

function openDeleteDialog(codeQ: CodingQuestionItem): void {
	deleteTargetCoding.value = codeQ
	showDeleteDialog.value = true
}

function handleConfirmDelete(): void {
	if (deleteTargetCoding.value) {
		emit('deleteCoding', deleteTargetCoding.value.id)
	}
	showDeleteDialog.value = false
	deleteTargetCoding.value = null
}

async function handleGenerateInlineAiCases(target: 'add' | 'edit'): Promise<void> {
	const title = target === 'add' ? newTitle.value : editTitle.value
	const problem = target === 'add' ? newProblem.value : editProblem.value
	const constraints = target === 'add' ? newConstraints.value : editConstraints.value

	if (!title.trim() || !problem.trim()) {
		notify({ color: 'warning', message: 'Enter problem title and description before generating AI cases.' })
		return
	}

	isGeneratingInlineAi.value = true
	try {
		const res = await api.post<{
			sample_test_cases: Array<{ input: string; expected_output: string }>
			hidden_test_cases: Array<{ input: string; expected_output: string }>
		}>(
			'/mentor/questions/coding/ai-generate-tests',
			{
				title,
				word_problem_text: problem,
				constraints_text: constraints,
			}
		)
		if (res.success && res.data) {
			const samples = res.data.sample_test_cases || getDefaultSampleCases()
			const hiddens = res.data.hidden_test_cases || getDefaultHiddenCases()

			if (target === 'add') {
				newSampleCases.value = samples
				newHiddenCases.value = hiddens
			} else {
				editSampleCases.value = samples
				editHiddenCases.value = hiddens
			}
			notify({
				color: 'success',
				message: `Synthesized ${samples.length} sample cases and ${hiddens.length} hidden test cases via AI.`,
			})
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Could not generate AI cases.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'AI generation error' })
	} finally {
		isGeneratingInlineAi.value = false
	}
}

function handleCommitImport(): void {
	if (selectedImportFile.value) {
		emit('importCoding', selectedImportFile.value)
	}
}
</script>

<template>
	<div class="pool-container">
		<div class="pool-header">
			<h2 class="section-title">Coding Problems</h2>
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
					Add Problem
				</VaButton>
			</div>
		</div>

		<div v-if="codingQuestions.length > 0" class="cards-list">
			<VaCard
				v-for="(codeQ, index) in codingQuestions"
				:key="codeQ.id"
				class="item-card"
			>
				<VaCardContent>
					<div class="card-inner">
						<div class="card-meta">
							<div class="meta-left">
								<VaBadge color="backgroundElement" :text="`P${index + 1}`" />
								<VaBadge
									:color="codeQ.difficulty === 'hard' ? 'danger' : codeQ.difficulty === 'medium' ? 'warning' : 'success'"
									:text="codeQ.difficulty.toUpperCase()"
								/>
								<XpStarBadge
									:points="codeQ.difficulty === 'hard' ? 50 : codeQ.difficulty === 'medium' ? 30 : 15"
									size="small"
								/>
								<span class="meta-tag"><VaIcon name="schedule" size="small" /> {{ codeQ.time_limit_ms }}ms</span>
								<span class="meta-tag"><VaIcon name="storage" size="small" /> {{ Math.round(codeQ.memory_limit_kb / 1024) }}MB</span>
							</div>

							<div v-if="!isPublished" class="meta-actions">
								<VaButton
									preset="plain"
									icon="edit"
									size="small"
									aria-label="Edit challenge"
									@click="openEditDialog(codeQ)"
								/>
								<VaButton
									preset="plain"
									icon="delete"
									color="danger"
									size="small"
									aria-label="Delete challenge"
									@click="openDeleteDialog(codeQ)"
								/>
							</div>
						</div>

						<h3 class="code-title">{{ codeQ.title }}</h3>

						<!-- Formatted Rich Text / Markdown problem description -->
						<div class="rendered-problem-wrapper">
							<MarkdownRenderer :content="codeQ.word_problem_text" />
						</div>

						<div v-if="codeQ.constraints_text" class="constraints-snippet">
							<strong>Constraints:</strong> {{ formatConstraints(codeQ.constraints_text) }}
						</div>

						<div class="card-action-bar">
							<VaBadge color="success" :text="`${getTestCaseCount(codeQ)} Verified Test Cases`">
								<template #prepend>
									<VaIcon name="check_circle" size="small" />
								</template>
							</VaBadge>
							<VaButton
								v-if="!isPublished"
								size="small"
								icon="auto_awesome"
								@click="emit('openAiGen', codeQ)"
							>
								Generate AI Stress Cases
							</VaButton>
						</div>
					</div>
				</VaCardContent>
			</VaCard>
		</div>

		<VaCard v-else class="empty-pool-card">
			<VaCardContent class="empty-content">
				<VaIcon name="code" size="48px" color="secondary" class="empty-pool-icon" />
				<h3>No Coding Problems added yet</h3>
				<p>Author or bulk import at least 7 coding challenges with 13 test cases (3 sample + 10 hidden) each to complete the set.</p>
			</VaCardContent>
		</VaCard>

		<!-- MODAL 1: CREATE CODING PROBLEM -->
		<VaModal
			v-model="showAddDialog"
			title="Create Algorithmic Coding Problem"
			ok-text="Save Problem"
			cancel-text="Cancel"
			:loading="isSubmitting"
			size="large"
			@ok="handleSaveAdd"
		>
			<VaForm class="dialog-form">
				<VaInput
					v-model="newTitle"
					label="Problem Title"
					placeholder="e.g. Subarray Sum Equals K"
					required
				/>

				<!-- Rich Text / Markdown Editor -->
				<RichTextEditor
					v-model="newProblem"
					label="Problem Statement (Rich Text / Markdown)"
					placeholder="Describe problem specifications, input format, output format, and examples..."
					:rows="6"
					required
				/>

				<VaTextarea
					v-model="newConstraints"
					label="Constraints"
					placeholder="e.g. 1 <= N <= 10^5"
					autosize
					:min-rows="2"
				/>

				<VaSelect
					v-model="newDifficulty"
					:options="difficultyOptions"
					label="Difficulty Tier"
					value-by="value"
					text-by="label"
				/>

				<!-- FUNCTION SIGNATURE & BOILERPLATE SPECIFICATION -->
				<div class="fn-signature-card">
					<div class="fn-signature-header">
						<div>
							<h4 class="testcases-heading">Function Signature & Template Configuration</h4>
							<p class="testcases-subheading">Defines the boilerplate harness method and starter code</p>
						</div>
					</div>

					<div class="fn-signature-row">
						<VaInput
							v-model="newFunctionName"
							label="Function Name"
							placeholder="e.g. solve"
							required
						/>
						<VaInput
							v-model="newReturnType"
							label="Return Type"
							placeholder="e.g. int, int[], string, void"
							required
						/>
					</div>

					<div class="fn-params-section">
						<div class="fn-params-header">
							<span class="group-title">Parameters</span>
							<VaButton
								preset="secondary"
								size="small"
								icon="add"
								@click="addParameterDef(false)"
							>
								Add Parameter
							</VaButton>
						</div>

						<div class="fn-params-list">
							<div
								v-for="(param, pIdx) in newParameterDefs"
								:key="'new-param-' + pIdx"
								class="fn-param-row"
							>
								<VaInput
									v-model="param.name"
									label="Param Name"
									placeholder="e.g. nums"
								/>
								<VaInput
									v-model="param.type"
									label="Param Type"
									placeholder="e.g. int[], int, string"
								/>
								<VaButton
									preset="danger"
									icon="delete"
									size="small"
									:disabled="newParameterDefs.length <= 1"
									@click="removeParameterDef(false, pIdx)"
								/>
							</div>
						</div>
					</div>
				</div>

				<div class="testcases-editor">
					<div class="testcases-header">
						<div>
							<h4 class="testcases-heading">Test Suite Configuration</h4>
							<p class="testcases-subheading">Configure 3 sample test cases and 10 hidden evaluation cases</p>
						</div>
						<VaButton
							preset="secondary"
							size="small"
							icon="auto_awesome"
							:loading="isGeneratingInlineAi"
							@click="handleGenerateInlineAiCases('add')"
						>
							Auto-Synthesize via AI
						</VaButton>
					</div>

					<!-- SECTION 1: SAMPLE TEST CASES -->
					<div class="testcase-group">
						<div class="group-header">
							<span class="group-title">Sample Test Cases</span>
							<VaBadge text="3 Required — Visible to Students" color="primary" class="group-badge" />
						</div>
						<div class="testcases-list">
							<VaCard
								v-for="(tc, i) in newSampleCases"
								:key="'new-sample-' + i"
								color="backgroundPrimary"
								class="tc-card"
							>
								<VaCardContent class="tc-content">
									<div class="tc-card-header">
										<span class="tc-tag sample-tag">Sample Case {{ i + 1 }}</span>
									</div>
									<div class="tc-grid">
										<VaTextarea
											v-model="tc.input"
											label="Standard Input"
											placeholder="Input stream"
											:rows="2"
											required
										/>
										<VaTextarea
											v-model="tc.expected_output"
											label="Expected Output"
											placeholder="Output stream"
											:rows="2"
											required
										/>
									</div>
								</VaCardContent>
							</VaCard>
						</div>
					</div>

					<!-- SECTION 2: HIDDEN TEST CASES -->
					<div class="testcase-group mt-3">
						<div class="group-header">
							<span class="group-title">Hidden Test Cases</span>
							<VaBadge text="10 Required — Standard Validation" color="warning" class="group-badge" />
						</div>
						<div class="testcases-list">
							<VaCard
								v-for="(tc, i) in newHiddenCases"
								:key="'new-hidden-' + i"
								color="backgroundPrimary"
								class="tc-card"
							>
								<VaCardContent class="tc-content">
									<div class="tc-card-header">
										<span class="tc-tag hidden-tag">Hidden Case {{ i + 1 }}</span>
									</div>
									<div class="tc-grid">
										<VaTextarea
											v-model="tc.input"
											label="Standard Input"
											placeholder="Input stream"
											:rows="2"
											required
										/>
										<VaTextarea
											v-model="tc.expected_output"
											label="Expected Output"
											placeholder="Output stream"
											:rows="2"
											required
										/>
									</div>
								</VaCardContent>
							</VaCard>
						</div>
					</div>
				</div>
			</VaForm>
		</VaModal>

		<!-- MODAL 2: EDIT CODING PROBLEM -->
		<VaModal
			v-model="showEditDialog"
			title="Edit Algorithmic Coding Problem"
			ok-text="Update Problem"
			cancel-text="Cancel"
			:loading="isSubmitting"
			size="large"
			@ok="handleSaveEdit"
		>
			<VaForm class="dialog-form">
				<VaInput
					v-model="editTitle"
					label="Problem Title"
					placeholder="e.g. Subarray Sum Equals K"
					required
				/>

				<RichTextEditor
					v-model="editProblem"
					label="Problem Statement (Rich Text / Markdown)"
					placeholder="Describe problem specifications, input format, output format, and examples..."
					:rows="6"
					required
				/>

				<VaTextarea
					v-model="editConstraints"
					label="Constraints"
					placeholder="e.g. 1 <= N <= 10^5"
					autosize
					:min-rows="2"
				/>

				<VaSelect
					v-model="editDifficulty"
					:options="difficultyOptions"
					label="Difficulty Tier"
					value-by="value"
					text-by="label"
				/>

				<!-- FUNCTION SIGNATURE & BOILERPLATE SPECIFICATION -->
				<div class="fn-signature-card">
					<div class="fn-signature-header">
						<div>
							<h4 class="testcases-heading">Function Signature & Template Configuration</h4>
							<p class="testcases-subheading">Defines the boilerplate harness method and starter code</p>
						</div>
					</div>

					<div class="fn-signature-row">
						<VaInput
							v-model="editFunctionName"
							label="Function Name"
							placeholder="e.g. solve"
							required
						/>
						<VaInput
							v-model="editReturnType"
							label="Return Type"
							placeholder="e.g. int, int[], string, void"
							required
						/>
					</div>

					<div class="fn-params-section">
						<div class="fn-params-header">
							<span class="group-title">Parameters</span>
							<VaButton
								preset="secondary"
								size="small"
								icon="add"
								@click="addParameterDef(true)"
							>
								Add Parameter
							</VaButton>
						</div>

						<div class="fn-params-list">
							<div
								v-for="(param, pIdx) in editParameterDefs"
								:key="'edit-param-' + pIdx"
								class="fn-param-row"
							>
								<VaInput
									v-model="param.name"
									label="Param Name"
									placeholder="e.g. nums"
								/>
								<VaInput
									v-model="param.type"
									label="Param Type"
									placeholder="e.g. int[], int, string"
								/>
								<VaButton
									preset="danger"
									icon="delete"
									size="small"
									:disabled="editParameterDefs.length <= 1"
									@click="removeParameterDef(true, pIdx)"
								/>
							</div>
						</div>
					</div>
				</div>

				<div class="testcases-editor">
					<div class="testcases-header">
						<div>
							<h4 class="testcases-heading">Test Suite Configuration</h4>
							<p class="testcases-subheading">Manage 3 sample test cases and 10 hidden evaluation cases</p>
						</div>
						<VaButton
							preset="secondary"
							size="small"
							icon="auto_awesome"
							:loading="isGeneratingInlineAi"
							@click="handleGenerateInlineAiCases('edit')"
						>
							Auto-Synthesize via AI
						</VaButton>
					</div>

					<!-- SECTION 1: SAMPLE TEST CASES -->
					<div class="testcase-group">
						<div class="group-header">
							<span class="group-title">Sample Test Cases</span>
							<VaBadge text="3 Required — Visible to Students" color="primary" class="group-badge" />
						</div>
						<div class="testcases-list">
							<VaCard
								v-for="(tc, i) in editSampleCases"
								:key="'edit-sample-' + i"
								color="backgroundPrimary"
								class="tc-card"
							>
								<VaCardContent class="tc-content">
									<div class="tc-card-header">
										<span class="tc-tag sample-tag">Sample Case {{ i + 1 }}</span>
									</div>
									<div class="tc-grid">
										<VaTextarea
											v-model="tc.input"
											label="Standard Input"
											placeholder="Input stream"
											:rows="2"
											required
										/>
										<VaTextarea
											v-model="tc.expected_output"
											label="Expected Output"
											placeholder="Output stream"
											:rows="2"
											required
										/>
									</div>
								</VaCardContent>
							</VaCard>
						</div>
					</div>

					<!-- SECTION 2: HIDDEN TEST CASES -->
					<div class="testcase-group mt-3">
						<div class="group-header">
							<span class="group-title">Hidden Test Cases</span>
							<VaBadge text="10 Required — Standard Validation" color="warning" class="group-badge" />
						</div>
						<div class="testcases-list">
							<VaCard
								v-for="(tc, i) in editHiddenCases"
								:key="'edit-hidden-' + i"
								color="backgroundPrimary"
								class="tc-card"
							>
								<VaCardContent class="tc-content">
									<div class="tc-card-header">
										<span class="tc-tag hidden-tag">Hidden Case {{ i + 1 }}</span>
									</div>
									<div class="tc-grid">
										<VaTextarea
											v-model="tc.input"
											label="Standard Input"
											placeholder="Input stream"
											:rows="2"
											required
										/>
										<VaTextarea
											v-model="tc.expected_output"
											label="Expected Output"
											placeholder="Output stream"
											:rows="2"
											required
										/>
									</div>
								</VaCardContent>
							</VaCard>
						</div>
					</div>
				</div>
			</VaForm>
		</VaModal>

		<!-- MODAL 3: DELETE CONFIRMATION -->
		<VaModal
			v-model="showDeleteDialog"
			title="Delete Coding Challenge"
			ok-text="Delete"
			cancel-text="Cancel"
			ok-color="danger"
			@ok="handleConfirmDelete"
		>
			<p v-if="deleteTargetCoding">
				Are you sure you want to remove this coding challenge and its test suite?
				<br />
				<strong>"{{ deleteTargetCoding.title }}"</strong>
			</p>
		</VaModal>

		<!-- MODAL 4: BULK IMPORT XLSX -->
		<VaModal
			v-model="showImportDialog"
			title="Bulk Import Coding Problems from Spreadsheet"
			hide-default-actions
		>
			<div class="import-modal-content">
				<p class="import-instruction">
					Upload an <code>.xlsx</code> or <code>.csv</code> spreadsheet containing coding challenges.
					Columns can include Title, Description, Constraints, and sample inputs/outputs.
					Any missing test cases will be <strong>automatically synthesized by AI</strong> to meet the mandatory 5 test cases standard.
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
						Import & Generate AI Tests
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
	gap: 1.25rem;
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
	gap: 0.65rem;
	flex-wrap: wrap;
}

.meta-actions {
	display: flex;
	align-items: center;
	gap: 0.25rem;
}

.meta-tag {
	font-size: 0.8rem;
	color: var(--va-text-secondary);
	display: inline-flex;
	align-items: center;
	gap: 0.25rem;
}

.code-title {
	margin: 0.25rem 0 0;
	font-size: 1.15rem;
	font-weight: 700;
	color: var(--va-text-primary);
}

.rendered-problem-wrapper {
	padding: 0.25rem 0;
}

.constraints-snippet {
	background-color: var(--va-background-element);
	border: 1px solid var(--va-background-border);
	padding: 0.5rem 0.75rem;
	border-radius: 4px;
	font-size: 0.85rem;
	color: var(--va-text-primary);
}

.card-action-bar {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-top: 0.5rem;
	flex-wrap: wrap;
	gap: 0.75rem;
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
	gap: 1.25rem;
	padding: 0.5rem 0;
}

.fn-signature-card {
	display: flex;
	flex-direction: column;
	gap: 0.75rem;
	background: var(--va-background-element);
	border: 1px solid var(--va-background-border);
	border-radius: 8px;
	padding: 0.85rem;
}

.fn-signature-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.fn-signature-row {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 0.75rem;
}

.fn-params-section {
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
	padding-top: 0.5rem;
	border-top: 1px dashed var(--va-background-border);
}

.fn-params-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.fn-params-list {
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
}

.fn-param-row {
	display: grid;
	grid-template-columns: 1fr 1fr auto;
	gap: 0.5rem;
	align-items: flex-end;
}

.testcases-editor {
	display: flex;
	flex-direction: column;
	gap: 0.75rem;
	border-top: 1px solid var(--va-background-border);
	padding-top: 1rem;
}

.testcases-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.testcases-heading {
	margin: 0;
	font-size: 0.95rem;
	font-weight: 700;
	color: var(--va-text-primary);
}

.testcases-subheading {
	margin: 0.15rem 0 0;
	font-size: 0.78rem;
	color: var(--va-text-secondary);
}

.testcase-group {
	display: flex;
	flex-direction: column;
	gap: 0.6rem;
	background: var(--va-background-element);
	border: 1px solid var(--va-background-border);
	border-radius: 8px;
	padding: 0.75rem;
}

.group-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding-bottom: 0.25rem;
	border-bottom: 1px dashed var(--va-background-border);
}

.group-title {
	font-size: 0.88rem;
	font-weight: 700;
	color: var(--va-text-primary);
}

.testcases-list {
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
}

.tc-card {
	border: 1px solid var(--va-background-border);
}

.tc-content {
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
	padding: 0.75rem;
}

.tc-card-header {
	display: flex;
	align-items: center;
}

.tc-tag {
	font-size: 0.72rem;
	font-weight: 700;
	text-transform: uppercase;
	padding: 0.15rem 0.5rem;
	border-radius: 4px;
	letter-spacing: 0.03em;
}

.sample-tag {
	background-color: rgba(var(--va-primary-rgb), 0.15);
	color: var(--va-primary);
	border: 1px solid rgba(var(--va-primary-rgb), 0.3);
}

.hidden-tag {
	background-color: rgba(var(--va-warning-rgb), 0.15);
	color: var(--va-warning);
	border: 1px solid rgba(var(--va-warning-rgb), 0.3);
}

.tc-grid {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 0.75rem;
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
