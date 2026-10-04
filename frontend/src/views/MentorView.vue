<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useToast } from 'vuestic-ui'

import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import type { QuestionSetData, FlaggedSubmission, CodingQuestionItem } from '@/types'
import RotationOverview from '@/components/mentor/RotationOverview.vue'
import McqPoolSection from '@/components/mentor/McqPoolSection.vue'
import CodingPoolSection from '@/components/mentor/CodingPoolSection.vue'
import AiStressTestDialog from '@/components/mentor/AiStressTestDialog.vue'
import FlaggedSubmissionsSection from '@/components/mentor/FlaggedSubmissionsSection.vue'

const { init: notify } = useToast()
const authStore = useAuthStore()

// Only users with the 'mentor' role can manage questions/publish
const isMentor = computed<boolean>(() => authStore.user?.role === 'mentor')

const isLoading = ref<boolean>(true)
const questionSet = ref<QuestionSetData | null>(null)
const flaggedSubmissions = ref<FlaggedSubmission[]>([])
const activeSection = ref<'mcqs' | 'coding' | 'flagged'>('mcqs')

const isPublishing = ref<boolean>(false)
const isSubmittingMcq = ref<boolean>(false)
const isSubmittingCoding = ref<boolean>(false)
const isImportingMcqs = ref<boolean>(false)
const isImportingCoding = ref<boolean>(false)

// AI Stress Test Dialog State
const showAiTestGenDialog = ref<boolean>(false)
const selectedCodingForAi = ref<CodingQuestionItem | null>(null)
const isGeneratingAiTests = ref<boolean>(false)
const generatedAiCases = ref<Array<{ input: string; expected_output: string; rationale?: string }>>([])

const mcqPoolCount = computed<number>(() => questionSet.value?.mcqs.length ?? 0)
const codingPoolCount = computed<number>(() => questionSet.value?.coding_questions.length ?? 0)
const isPublished = computed<boolean>(() => questionSet.value?.status === 'published')

async function fetchQuestionSet(): Promise<void> {
	try {
		const res = await api.get<QuestionSetData>('/mentor/question-set/my-week')
		if (res.success && res.data) {
			questionSet.value = res.data
		}
	} catch {
		notify({ color: 'info', message: 'No active question set found for this week.' })
	}
}

async function fetchFlaggedSubmissions(): Promise<void> {
	try {
		const res = await api.get<FlaggedSubmission[]>('/mentor/flagged-submissions')
		if (res.success && res.data) {
			flaggedSubmissions.value = res.data
		}
	} catch {
		// Silent error
	}
}

async function handlePublish(): Promise<void> {
	if (!questionSet.value) return
	isPublishing.value = true
	try {
		const res = await api.post<QuestionSetData>(`/mentor/question-set/${questionSet.value.id}/publish`)
		if (res.success && res.data) {
			questionSet.value = res.data
			notify({ color: 'success', message: 'Question set successfully published and locked for rotation!' })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Failed to publish question set.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Network error' })
	} finally {
		isPublishing.value = false
	}
}

async function handleAddMcq(payload: {
	prompt_text: string
	options: string[]
	correct_option_index: number
	explanation?: string
	difficulty: string
}): Promise<void> {
	isSubmittingMcq.value = true
	try {
		const res = await api.post<QuestionSetData>('/mentor/questions/mcq', {
			question_set_id: questionSet.value?.id,
			...payload,
		})
		if (res.success && res.data) {
			questionSet.value = res.data
			notify({ color: 'success', message: 'MCQ added to question pool.' })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Failed to add MCQ.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Network error' })
	} finally {
		isSubmittingMcq.value = false
	}
}

async function handleUpdateMcq(mcqId: number, payload: {
	prompt_text: string
	options: string[]
	correct_option_index: number
	explanation?: string
	difficulty: string
}): Promise<void> {
	try {
		const res = await api.put<QuestionSetData>(`/mentor/questions/mcq/${mcqId}`, payload)
		if (res.success && res.data) {
			questionSet.value = res.data
			notify({ color: 'success', message: 'MCQ updated successfully.' })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Failed to update MCQ.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Update error' })
	}
}

async function handleDeleteMcq(mcqId: number): Promise<void> {
	try {
		const res = await api.delete<QuestionSetData>(`/mentor/questions/mcq/${mcqId}`)
		if (res.success && res.data) {
			questionSet.value = res.data
			notify({ color: 'success', message: 'MCQ removed from pool.' })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Failed to delete MCQ.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Delete error' })
	}
}

async function handleImportMcqs(file: File): Promise<void> {
	isImportingMcqs.value = true
	try {
		const formData = new FormData()
		formData.append('file', file)
		if (questionSet.value) {
			formData.append('question_set_id', questionSet.value.id.toString())
		}

		const res = await api.upload<QuestionSetData>('/mentor/questions/import-mcq-sheet', formData)
		if (res.success && res.data) {
			questionSet.value = res.data
			notify({ color: 'success', message: res.message || 'MCQs successfully imported via AI!' })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Failed to import MCQs.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Import error' })
	} finally {
		isImportingMcqs.value = false
	}
}

async function handleAddCoding(payload: {
	title: string
	word_problem_text: string
	constraints_text: string
	difficulty: string
	sample_test_cases: Array<{ input: string; expected_output: string }>
	hidden_test_cases: Array<{ input: string; expected_output: string }>
	function_name?: string
	parameter_definitions?: Array<{ name: string; type: string }>
	return_type?: string
	starter_templates?: Record<string, string>
}): Promise<void> {
	isSubmittingCoding.value = true
	try {
		const res = await api.post<QuestionSetData>('/mentor/questions/coding', {
			question_set_id: questionSet.value?.id,
			...payload,
		})
		if (res.success && res.data) {
			questionSet.value = res.data
			notify({ color: 'success', message: 'Coding challenge added with 3 sample and 10 hidden test cases.' })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Failed to add coding question.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Network error' })
	} finally {
		isSubmittingCoding.value = false
	}
}

async function handleUpdateCoding(codingId: number, payload: {
	title: string
	word_problem_text: string
	constraints_text: string
	difficulty: string
	sample_test_cases: Array<{ input: string; expected_output: string }>
	hidden_test_cases: Array<{ input: string; expected_output: string }>
	function_name?: string
	parameter_definitions?: Array<{ name: string; type: string }>
	return_type?: string
	starter_templates?: Record<string, string>
}): Promise<void> {
	try {
		const res = await api.put<QuestionSetData>(`/mentor/questions/coding/${codingId}`, payload)
		if (res.success && res.data) {
			questionSet.value = res.data
			notify({ color: 'success', message: 'Coding challenge updated successfully.' })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Failed to update coding challenge.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Update error' })
	}
}

async function handleDeleteCoding(codingId: number): Promise<void> {
	try {
		const res = await api.delete<QuestionSetData>(`/mentor/questions/coding/${codingId}`)
		if (res.success && res.data) {
			questionSet.value = res.data
			notify({ color: 'success', message: 'Coding challenge removed from pool.' })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Failed to delete coding challenge.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Delete error' })
	}
}

async function handleImportCoding(file: File): Promise<void> {
	isImportingCoding.value = true
	try {
		const formData = new FormData()
		formData.append('file', file)
		if (questionSet.value) {
			formData.append('question_set_id', questionSet.value.id.toString())
		}

		const res = await api.upload<QuestionSetData>('/mentor/questions/import-coding-sheet', formData)
		if (res.success && res.data) {
			questionSet.value = res.data
			notify({ color: 'success', message: res.message || 'Coding challenges and AI test cases imported!' })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Failed to import coding challenges.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Import error' })
	} finally {
		isImportingCoding.value = false
	}
}

function openAiTestGen(question: CodingQuestionItem): void {
	selectedCodingForAi.value = question
	generatedAiCases.value = []
	showAiTestGenDialog.value = true
}

async function triggerAiGeneration(): Promise<void> {
	if (!selectedCodingForAi.value) return
	isGeneratingAiTests.value = true
	try {
		const res = await api.post<{ test_cases: Array<{ input: string; expected_output: string; rationale?: string }> }>(
			`/mentor/coding/${selectedCodingForAi.value.id}/generate-ai-tests`
		)
		if (res.success && res.data) {
			generatedAiCases.value = res.data.test_cases
			notify({ color: 'success', message: `Synthesized ${res.data.test_cases.length} AI edge cases.` })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'AI test generation failed.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Generation network error' })
	} finally {
		isGeneratingAiTests.value = false
	}
}

async function handleAcceptAiCases(cases: Array<{ input: string; expected_output: string }>): Promise<void> {
	if (!selectedCodingForAi.value) return
	try {
		const res = await api.post<QuestionSetData>(
			`/mentor/coding/${selectedCodingForAi.value.id}/append-test-cases`,
			{ test_cases: cases }
		)
		if (res.success && res.data) {
			questionSet.value = res.data
			showAiTestGenDialog.value = false
			notify({ color: 'success', message: `Appended ${cases.length} AI cases to test suite.` })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Failed to save test cases' })
	}
}

async function handleResolveSubmission(payload: { submissionId: number; resolution: 'dismiss' | 'action' }): Promise<void> {
	try {
		const res = await api.post<{ message: string }>(
			`/mentor/flagged-submissions/${payload.submissionId}/resolve`,
			{ resolution: payload.resolution }
		)
		if (res.success) {
			flaggedSubmissions.value = flaggedSubmissions.value.filter((s: FlaggedSubmission) => s.id !== payload.submissionId)
			notify({ color: 'success', message: res.data?.message || 'Resolved flagged submission.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Action failed' })
	}
}

onMounted(async (): Promise<void> => {
	await Promise.all([fetchQuestionSet(), fetchFlaggedSubmissions()])
	isLoading.value = false
})
</script>

<template>
	<div class="mentor-page">
		<RotationOverview
			:questionSet="questionSet"
			:mcqCount="mcqPoolCount"
			:codingCount="codingPoolCount"
			:isPublishing="isPublishing"
			@publish="handlePublish"
		/>

		<!-- Sub-navigation between Pools & AI Review Queue — mentor only -->
		<template v-if="isMentor">
			<div class="section-switch-bar">
				<VaTabs v-model="activeSection">
					<VaTab name="mcqs">
						<span class="tab-item-content">
							<VaIcon name="list" size="small" />
							<span>Aptitude MCQs ({{ mcqPoolCount }})</span>
						</span>
					</VaTab>
					<VaTab name="coding">
						<span class="tab-item-content">
							<VaIcon name="code" size="small" />
							<span>Coding Problems ({{ codingPoolCount }})</span>
						</span>
					</VaTab>
					<VaTab name="flagged">
						<span class="tab-item-content">
							<VaIcon name="flag" size="small" />
							<span>AI Flagged Review ({{ flaggedSubmissions.length }})</span>
						</span>
					</VaTab>
				</VaTabs>
			</div>

			<!-- SECTION 1: MCQ POOL -->
			<McqPoolSection
				v-if="activeSection === 'mcqs'"
				:mcqs="questionSet?.mcqs || []"
				:isPublished="isPublished"
				:isSubmitting="isSubmittingMcq"
				:isImporting="isImportingMcqs"
				@addMcq="handleAddMcq"
				@updateMcq="handleUpdateMcq"
				@deleteMcq="handleDeleteMcq"
				@importMcqs="handleImportMcqs"
			/>

			<!-- SECTION 2: CODING POOL -->
			<CodingPoolSection
				v-if="activeSection === 'coding'"
				:codingQuestions="questionSet?.coding_questions || []"
				:isPublished="isPublished"
				:isSubmitting="isSubmittingCoding"
				:isImporting="isImportingCoding"
				@addCoding="handleAddCoding"
				@updateCoding="handleUpdateCoding"
				@deleteCoding="handleDeleteCoding"
				@openAiGen="openAiTestGen"
				@importCoding="handleImportCoding"
			/>

			<!-- SECTION 3: FLAGGED SUBMISSIONS REVIEW -->
			<FlaggedSubmissionsSection
				v-if="activeSection === 'flagged'"
				:flaggedSubmissions="flaggedSubmissions"
				:isSubmitting="false"
				@resolve="handleResolveSubmission"
			/>

			<!-- AI Stress Test Dialog -->
			<AiStressTestDialog
				v-model:visible="showAiTestGenDialog"
				:question="selectedCodingForAi"
				:isGenerating="isGeneratingAiTests"
				:generatedCases="generatedAiCases"
				@generate="triggerAiGeneration"
				@accept="handleAcceptAiCases"
			/>
		</template>

		<!-- Students see only the rotation overview — no question management -->
		<VaCard v-else class="student-mentor-notice">
			<VaCardContent>
				<div class="notice-row">
					<VaIcon name="info" color="info" />
					<span>Question management is available to mentors only. Your rotation overview is shown above.</span>
				</div>
			</VaCardContent>
		</VaCard>
	</div>
</template>

<style scoped>
.mentor-page {
	max-width: 1400px;
	margin: 0 auto;
	padding: 1.5rem;
	width: 100%;
}

.section-switch-bar {
	margin-bottom: 1.5rem;
}

.tab-item-content {
	display: inline-flex;
	align-items: center;
	gap: 0.5rem;
}

.student-mentor-notice {
	border: 1px solid var(--va-background-border);
}

.notice-row {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	font-size: 0.9rem;
	color: var(--va-text-secondary);
}
</style>
