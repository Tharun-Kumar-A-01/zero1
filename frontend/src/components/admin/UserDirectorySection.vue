<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { UserItem, ImportJobResponse } from '@/types'
import UserProfileModal from '@/components/UserProfileModal.vue'

const props = defineProps<{
	users: UserItem[]
	isCreating: boolean
	isUpdating?: boolean
	isUploadingSheet?: boolean
	isCommittingImport?: boolean
	importJob?: ImportJobResponse | null
	importSummary?: { imported_count: number; skipped_count: number; errors: string[] } | null
}>()

const emit = defineEmits<{
	(e: 'createUser', payload: { name: string; email: string; role: 'student' | 'mentor' | 'admin'; password: string }): void
	(e: 'updateUser', userId: number, payload: { name: string; email: string; role: 'student' | 'mentor' | 'admin'; password?: string }): void
	(e: 'uploadRoster', file: File, year: string): void
	(e: 'commitRoster', mapping: Record<string, number>): void
}>()

const filterRole = ref<string>('all')
const searchQuery = ref<string>('')
const currentPage = ref<number>(1)
const perPage = ref<number>(10)

// Create User state
const showCreateDialog = ref<boolean>(false)
const newName = ref<string>('')
const newEmail = ref<string>('')
const newRole = ref<'student' | 'mentor' | 'admin'>('student')
const newPassword = ref<string>('DefaultPassword@123')

// Edit User state
const showEditDialog = ref<boolean>(false)
const editUserId = ref<number | null>(null)
const editName = ref<string>('')
const editEmail = ref<string>('')
const editRole = ref<'student' | 'mentor' | 'admin'>('student')
const editPassword = ref<string>('')

// Profile Modal state
const showProfileDialog = ref<boolean>(false)
const selectedProfileUser = ref<UserItem | null>(null)

// Roster Import Modal state
const showImportDialog = ref<boolean>(false)
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

const roleOptions = [
	{ label: 'Student', value: 'student' },
	{ label: 'Mentor', value: 'mentor' },
	{ label: 'Admin', value: 'admin' },
]

const columns = [
	{ key: 'name', label: 'User', sortable: true },
	{ key: 'role', label: 'Role', sortable: true },
	{ key: 'roll_number', label: 'Roll Number', sortable: true },
	{ key: 'year_batch', label: 'Batch', sortable: true },
	{ key: 'section', label: 'Section' },
	{ key: 'is_active', label: 'Status', sortable: true },
	{ key: 'actions', label: 'Actions' },
]

const filteredUsers = computed<UserItem[]>(() => {
	let list = props.users
	if (filterRole.value !== 'all') {
		list = list.filter((u) => u.role === filterRole.value)
	}
	if (searchQuery.value.trim()) {
		const q = searchQuery.value.toLowerCase()
		list = list.filter((u) => u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q) || (u.roll_number && u.roll_number.toLowerCase().includes(q)))
	}
	return list
})

const totalPages = computed(() => Math.ceil(filteredUsers.value.length / perPage.value) || 1)

function handleCreate(): void {
	if (!newName.value.trim() || !newEmail.value.trim()) return
	emit('createUser', {
		name: newName.value,
		email: newEmail.value,
		role: newRole.value,
		password: newPassword.value,
	})
	showCreateDialog.value = false
	newName.value = ''
	newEmail.value = ''
	newPassword.value = 'DefaultPassword@123'
}

function openEditModal(user: UserItem): void {
	editUserId.value = user.id
	editName.value = user.name
	editEmail.value = user.email
	editRole.value = user.role
	editPassword.value = ''
	showEditDialog.value = true
}

function handleUpdate(): void {
	if (!editUserId.value || !editName.value.trim() || !editEmail.value.trim()) return
	emit('updateUser', editUserId.value, {
		name: editName.value,
		email: editEmail.value,
		role: editRole.value,
		password: editPassword.value.trim() || undefined,
	})
	showEditDialog.value = false
}

function openProfileModal(user: UserItem): void {
	selectedProfileUser.value = user
	showProfileDialog.value = true
}

function handleUpload(): void {
	if (selectedFile.value && targetYearBatch.value.trim()) {
		emit('uploadRoster', selectedFile.value, targetYearBatch.value)
	}
}

function handleCommit(): void {
	emit('commitRoster', customColumnMapping.value)
}
</script>

<template>
	<div class="users-container">
		<div class="users-header">
			<h2 class="section-title">Users Directory</h2>
			<div class="header-actions">
				<VaButton
					size="small"
					icon="upload_file"
					preset="secondary"
					@click="showImportDialog = true"
				>
					Import Roster
				</VaButton>
				<VaButton
					size="small"
					icon="person_add"
					@click="showCreateDialog = true"
				>
					Add User
				</VaButton>
			</div>
		</div>

		<!-- Filter Bar -->
		<div class="directory-filter-bar">
			<VaTabs v-model="filterRole">
				<VaTab name="all">All Roles ({{ users.length }})</VaTab>
				<VaTab name="student">Students</VaTab>
				<VaTab name="mentor">Mentors</VaTab>
				<VaTab name="admin">Admins</VaTab>
			</VaTabs>

			<div class="search-box">
				<VaInput
					v-model="searchQuery"
					placeholder="Search by name, email, roll..."
					clearable
				>
					<template #prependInner>
						<VaIcon name="search" size="small" />
					</template>
				</VaInput>
			</div>
		</div>

		<!-- User Data Table -->
		<VaCard v-if="filteredUsers.length > 0">
			<VaCardContent>
				<VaDataTable
					:items="filteredUsers"
					:columns="columns"
					:per-page="perPage"
					:current-page="currentPage"
					striped
					hoverable
				>
					<template #cell(name)="{ rowData }">
						<div class="user-cell clickable-user" @click="openProfileModal(rowData as UserItem)">
							<VaAvatar size="small" color="primary">
								{{ (rowData as UserItem).name.charAt(0).toUpperCase() }}
							</VaAvatar>
							<div class="user-details">
								<span class="user-name">{{ (rowData as UserItem).name }}</span>
								<span class="user-email">{{ (rowData as UserItem).email }}</span>
							</div>
						</div>
					</template>

					<template #cell(role)="{ rowData }">
						<VaBadge
							:text="(rowData as UserItem).role.toUpperCase()"
							:color="(rowData as UserItem).role === 'admin' ? 'danger' : (rowData as UserItem).role === 'mentor' ? 'warning' : 'primary'"
						/>
					</template>

					<template #cell(roll_number)="{ rowData }">
						<span>{{ (rowData as UserItem).roll_number || '—' }}</span>
					</template>

					<template #cell(year_batch)="{ rowData }">
						<span>{{ (rowData as UserItem).year_batch ? `Batch ${(rowData as UserItem).year_batch}` : '—' }}</span>
					</template>

					<template #cell(section)="{ rowData }">
						<span>{{ (rowData as UserItem).section || '—' }}</span>
					</template>

					<template #cell(is_active)="{ rowData }">
						<VaBadge
							:text="(rowData as UserItem).is_active ? 'ACTIVE' : 'INACTIVE'"
							:color="(rowData as UserItem).is_active ? 'success' : 'secondary'"
						/>
					</template>

					<template #cell(actions)="{ rowData }">
						<VaButton
							size="small"
							preset="plain"
							icon="edit"
							title="Edit User"
							@click="openEditModal(rowData as UserItem)"
						/>
					</template>
				</VaDataTable>

				<div v-if="totalPages > 1" class="table-pagination">
					<VaPagination
						v-model="currentPage"
						:pages="totalPages"
						:visible-pages="5"
					/>
				</div>
			</VaCardContent>
		</VaCard>

		<VaCard v-else class="empty-state-card">
			<VaCardContent class="empty-content">
				<VaIcon name="search" size="48px" color="secondary" class="empty-icon" />
				<h3>No users match your filter</h3>
				<p>Try searching with another keyword or resetting the role filter.</p>
			</VaCardContent>
		</VaCard>

		<!-- CREATE USER MODAL -->
		<VaModal
			v-model="showCreateDialog"
			title="Create User Account"
			ok-text="Create Account"
			cancel-text="Cancel"
			:loading="isCreating"
			@ok="handleCreate"
		>
			<VaForm class="dialog-form">
				<VaInput
					v-model="newName"
					label="Full Name"
					placeholder="John Doe"
					required
				/>

				<VaInput
					v-model="newEmail"
					type="email"
					label="Email Address"
					placeholder="john.doe@dept.edu"
					required
				/>

				<VaSelect
					v-model="newRole"
					:options="roleOptions"
					label="Account Role"
					value-by="value"
					text-by="label"
					required
				/>

				<VaInput
					v-model="newPassword"
					type="password"
					label="Temporary Password"
					required
				/>
			</VaForm>
		</VaModal>

		<!-- EDIT USER MODAL -->
		<VaModal
			v-model="showEditDialog"
			title="Edit User Account"
			ok-text="Save Changes"
			cancel-text="Cancel"
			:loading="isUpdating"
			@ok="handleUpdate"
		>
			<VaForm class="dialog-form">
				<VaInput
					v-model="editName"
					label="Full Name"
					required
				/>

				<VaInput
					v-model="editEmail"
					type="email"
					label="Email Address"
					required
				/>

				<VaSelect
					v-model="editRole"
					:options="roleOptions"
					label="Account Role"
					value-by="value"
					text-by="label"
					required
				/>

				<VaInput
					v-model="editPassword"
					type="password"
					label="New Password (optional)"
					placeholder="Leave blank to keep unchanged"
				/>
			</VaForm>
		</VaModal>

		<!-- INLINE ROSTER IMPORT MODAL -->
		<VaModal
			v-model="showImportDialog"
			title="Import Student Roster (.xlsx / .csv)"
			hide-default-actions
			size="large"
		>
			<div class="modal-import-workflow">
				<!-- Step 1: File & Target Year Upload -->
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
							:loading="isUploadingSheet"
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
						<h4 class="subsection-title">Column Mapping</h4>
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
						<span class="preview-title">Sample Data Preview</span>
						<VaDataTable
							:items="sampleTableItems"
							:columns="sampleTableColumns"
							striped
							hoverable
						/>
					</div>

					<div class="commit-action">
						<VaButton
							:loading="isCommittingImport"
							icon="check"
							@click="handleCommit"
						>
							Confirm & Import Roster
						</VaButton>
					</div>
				</div>

				<!-- Step 3: Import Results -->
				<div v-if="importSummary" class="summary-section">
					<div class="summary-head">
						<VaIcon name="check_circle" color="success" size="large" />
						<h4 class="summary-title">Import Summary</h4>
					</div>

					<div class="summary-stats-row">
						<VaBadge
							:text="`${importSummary.imported_count} Students Imported`"
							color="success"
						/>
						<VaBadge
							v-if="importSummary.skipped_count > 0"
							:text="`${importSummary.skipped_count} Skipped / Duplicates`"
							color="warning"
						/>
					</div>

					<VaAlert v-if="importSummary.errors.length > 0" color="danger" border="left" class="errors-alert">
						<template #icon>
							<VaIcon name="warning" />
						</template>
						<div class="errors-box">
							<strong class="errors-title">Skipped Entries Log:</strong>
							<ul class="errors-list">
								<li v-for="(err, eIdx) in importSummary.errors" :key="eIdx">{{ err }}</li>
							</ul>
						</div>
					</VaAlert>
				</div>

				<div class="modal-footer">
					<VaButton preset="secondary" @click="showImportDialog = false">
						Close
					</VaButton>
				</div>
			</div>
		</VaModal>

		<!-- USER PROFILE MODAL -->
		<UserProfileModal
			v-model="showProfileDialog"
			:user="selectedProfileUser"
		/>
	</div>
</template>

<style scoped>
.users-container {
	display: flex;
	flex-direction: column;
	gap: 1.25rem;
}

.users-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.section-title {
	font-size: 1.25rem;
	font-weight: 700;
	color: var(--va-text-primary);
	margin: 0;
}

.header-actions {
	display: flex;
	gap: 0.75rem;
	align-items: center;
}

.directory-filter-bar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	flex-wrap: wrap;
	gap: 1rem;
}

.search-box {
	min-width: 280px;
}

.user-cell {
	display: flex;
	align-items: center;
	gap: 0.75rem;
}

.clickable-user {
	cursor: pointer;
}

.user-details {
	display: flex;
	flex-direction: column;
}

.user-name {
	font-weight: 600;
	color: var(--va-text-primary);
}

.user-email {
	font-size: 0.8125rem;
	color: var(--va-secondary);
}

.table-pagination {
	display: flex;
	justify-content: center;
	padding-top: 1rem;
}

.dialog-form {
	display: flex;
	flex-direction: column;
	gap: 1rem;
	padding: 0.5rem 0;
}

.modal-import-workflow {
	display: flex;
	flex-direction: column;
	gap: 1.25rem;
	padding: 0.5rem 0;
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
	min-width: 240px;
}

.action-field {
	display: flex;
	align-items: center;
}

.mapping-section,
.summary-section {
	display: flex;
	flex-direction: column;
	gap: 1rem;
	border-top: 1px solid var(--va-background-border);
	padding-top: 1rem;
}

.mapping-header,
.summary-head {
	display: flex;
	align-items: center;
	gap: 0.75rem;
}

.subsection-title,
.summary-title {
	font-size: 1rem;
	font-weight: 600;
	margin: 0;
	color: var(--va-text-primary);
}

.mapping-selectors {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
	gap: 0.75rem;
}

.sample-preview {
	display: flex;
	flex-direction: column;
	gap: 0.375rem;
}

.preview-title {
	font-size: 0.8125rem;
	font-weight: 600;
	color: var(--va-secondary);
}

.commit-action {
	display: flex;
	justify-content: flex-end;
}

.summary-stats-row {
	display: flex;
	gap: 0.5rem;
	flex-wrap: wrap;
}

.errors-alert {
	margin-top: 0.25rem;
}

.errors-box {
	display: flex;
	flex-direction: column;
	gap: 0.25rem;
}

.errors-title {
	font-size: 0.8125rem;
}

.errors-list {
	margin: 0;
	padding-left: 1rem;
	font-size: 0.75rem;
}

.modal-footer {
	display: flex;
	justify-content: flex-end;
	margin-top: 1rem;
	border-top: 1px solid var(--va-background-border);
	padding-top: 0.75rem;
}
</style>
