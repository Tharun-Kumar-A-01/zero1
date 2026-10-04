<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { ImportJobResponse } from '@/types'

const props = defineProps<{
	isUploading: boolean
	isCommitting: boolean
	importJob: ImportJobResponse | null
	summary: { imported_count: number; skipped_count: number; errors: string[] } | null
}>()

const emit = defineEmits<{
	(e: 'upload', file: File, targetYear: string): void
	(e: 'commit', mapping: Record<string, number>): void
}>()

const targetYearBatch = ref<string>('2026')
const uploadedFiles = ref<File | File[] | undefined>(undefined)
const selectedFile = computed<File | null>(() => {
	const val = uploadedFiles.value
	if (!val) return null
	if (Array.isArray(val)) {
		return val.length > 0 ? (val[0] ?? null) : null
	}
	if (typeof val === 'object' && 'name' in val) {
		return val as File
	}
	return null
})

function handleFileChange(): void {
	if (document.activeElement instanceof HTMLElement) {
		document.activeElement.blur()
	}
}

const customColumnMapping = ref<Record<string, number>>({
	name: 0,
	email: 1,
	roll_number: 2,
})

watch(
	() => props.importJob,
	(newJob) => {
		if (newJob?.inferred_mapping?.column_mapping) {
			customColumnMapping.value = { ...newJob.inferred_mapping.column_mapping }
		}
	},
	{ immediate: true }
)

const columnDropdownOptions = computed<Array<{ label: string; value: number }>>(() => {
	const firstRow = props.importJob?.sample_grid?.[0]
	if (!firstRow) return []
	return firstRow.map((h, i) => ({ label: `Col ${i + 1}: ${h || 'Column ' + (i + 1)}`, value: i }))
})

const sampleTableColumns = computed(() => {
	const firstRow = props.importJob?.sample_grid?.[0]
	if (!firstRow) return []
	return firstRow.map((col, idx) => ({
		key: `col_${idx}`,
		label: `Col ${idx + 1}: ${col || 'Col ' + (idx + 1)}`,
	}))
})

const sampleTableItems = computed(() => {
	if (!props.importJob) return []
	const { sample_grid, inferred_mapping } = props.importJob
	const rows = sample_grid.slice(inferred_mapping.data_row_start_index, inferred_mapping.data_row_start_index + 6)
	return rows.map((row) => {
		const rowObj: Record<string, string> = {}
		row.forEach((val, idx) => {
			rowObj[`col_${idx}`] = val || '—'
		})
		return rowObj
	})
})

function handleUpload(): void {
	if (selectedFile.value && targetYearBatch.value.trim()) {
		emit('upload', selectedFile.value, targetYearBatch.value)
	}
}

function handleCommit(): void {
	emit('commit', customColumnMapping.value)
}
</script>

<template>
	<div class="import-container">
		<div class="section-header">
			<h2 class="section-title">Student Roster Import</h2>
		</div>

		<!-- Single Clean Upload Card -->
		<VaCard class="upload-main-card">
			<VaCardContent>
				<div class="upload-controls-layout">
					<div class="batch-field">
						<VaInput
							v-model="targetYearBatch"
							label="Target Year Batch"
							placeholder="e.g. 2026"
						/>
					</div>

					<div class="file-field">
						<VaFileUpload
							v-model="uploadedFiles"
							dropzone
							file-types=".xlsx,.csv"
							type="single"
							@update:model-value="handleFileChange"
						/>
					</div>

					<div class="action-field">
						<VaButton
							:loading="isUploading"
							:disabled="!selectedFile || !targetYearBatch.trim()"
							icon="auto_awesome"
							@click="handleUpload"
						>
							Analyze Spreadsheet
						</VaButton>
					</div>
				</div>

				<!-- Step 2: Mapping Configuration (Flat panel) -->
				<div v-if="importJob" class="mapping-section">
					<div class="mapping-header">
						<h3 class="subsection-title">Column Mapping</h3>
						<VaBadge
							:text="`AI Confidence: ${Math.round((importJob.inferred_mapping.confidence || 0) * 100)}%`"
							color="success"
						/>
					</div>

					<div class="mapping-selectors">
						<VaSelect
							v-model="customColumnMapping.name"
							:options="columnDropdownOptions"
							label="Full Name Column"
							value-by="value"
							text-by="label"
						/>
						<VaSelect
							v-model="customColumnMapping.email"
							:options="columnDropdownOptions"
							label="Email Address Column"
							value-by="value"
							text-by="label"
						/>
						<VaSelect
							v-model="customColumnMapping.roll_number"
							:options="columnDropdownOptions"
							label="Roll Number Column"
							value-by="value"
							text-by="label"
						/>
					</div>

					<!-- Sample Data Preview -->
					<div class="sample-preview">
						<h4 class="preview-title">Sample Data Preview</h4>
						<VaDataTable
							:items="sampleTableItems"
							:columns="sampleTableColumns"
							striped
							hoverable
						/>
					</div>

					<div class="commit-action">
						<VaButton
							:loading="isCommitting"
							icon="check"
							@click="handleCommit"
						>
							Confirm & Import Roster
						</VaButton>
					</div>
				</div>

				<!-- Step 3: Import Results (Flat panel) -->
				<div v-if="summary" class="summary-section">
					<div class="summary-head">
						<VaIcon name="check_circle" color="success" size="large" />
						<h3 class="summary-title">Import Summary</h3>
					</div>

					<div class="summary-stats-row">
						<VaBadge
							:text="`${summary.imported_count} Students Imported`"
							color="success"
						/>
						<VaBadge
							v-if="summary.skipped_count > 0"
							:text="`${summary.skipped_count} Skipped / Duplicates`"
							color="warning"
						/>
					</div>

					<VaAlert v-if="summary.errors.length > 0" color="danger" border="left" class="errors-alert">
						<template #icon>
							<VaIcon name="warning" />
						</template>
						<div class="errors-box">
							<strong class="errors-title">Skipped Entries Log:</strong>
							<ul class="errors-list">
								<li v-for="(err, eIdx) in summary.errors" :key="eIdx">{{ err }}</li>
							</ul>
						</div>
					</VaAlert>
				</div>
			</VaCardContent>
		</VaCard>
	</div>
</template>

<style scoped>
.import-container {
	display: flex;
	flex-direction: column;
	gap: 1rem;
}

.section-header {
	margin-bottom: 0.5rem;
}

.section-title {
	font-size: 1.25rem;
	font-weight: 700;
	margin: 0;
	color: var(--va-text-primary);
}

.upload-main-card {
	border: 1px solid var(--va-background-border);
}

.upload-controls-layout {
	display: flex;
	align-items: center;
	gap: 1.25rem;
	flex-wrap: wrap;
}

.batch-field {
	width: 140px;
}

.file-field {
	flex: 1;
	min-width: 260px;
}

.action-field {
	display: flex;
	align-items: center;
}

.mapping-section,
.summary-section {
	margin-top: 1.5rem;
	padding-top: 1.5rem;
	border-top: 1px solid var(--va-background-border);
	display: flex;
	flex-direction: column;
	gap: 1.25rem;
}

.mapping-header,
.summary-head {
	display: flex;
	align-items: center;
	gap: 0.75rem;
}

.subsection-title,
.summary-title {
	font-size: 1.125rem;
	font-weight: 600;
	margin: 0;
	color: var(--va-text-primary);
}

.mapping-selectors {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
	gap: 1rem;
}

.sample-preview {
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
}

.preview-title {
	font-size: 0.875rem;
	font-weight: 600;
	color: var(--va-secondary);
	margin: 0;
}

.commit-action {
	display: flex;
	justify-content: flex-end;
}

.summary-stats-row {
	display: flex;
	gap: 0.75rem;
	flex-wrap: wrap;
}

.errors-alert {
	margin-top: 0.5rem;
}

.errors-box {
	display: flex;
	flex-direction: column;
	gap: 0.25rem;
}

.errors-title {
	font-size: 0.875rem;
}

.errors-list {
	margin: 0;
	padding-left: 1.25rem;
	font-size: 0.8125rem;
}
</style>
