<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useToast } from 'vuestic-ui'

import api from '@/services/api'
import type { UserItem, RotationItem, CustomLeaveItem, ImportJobResponse } from '@/types'
import AdminHubBanner from '@/components/admin/AdminHubBanner.vue'
import MentorScheduleSection from '@/components/admin/MentorScheduleSection.vue'
import UserDirectorySection from '@/components/admin/UserDirectorySection.vue'

const { init: notify } = useToast()

const activeTab = ref<'rotations' | 'users'>('users')
const isLoading = ref<boolean>(true)

// User Management
const users = ref<UserItem[]>([])
const isCreatingUser = ref<boolean>(false)
const isUpdatingUser = ref<boolean>(false)

// Mentor Rotations
const rotations = ref<RotationItem[]>([])
const isScheduling = ref<boolean>(false)

// Department Leaves
const leaves = ref<CustomLeaveItem[]>([])
const isCreatingLeave = ref<boolean>(false)
const isDeletingLeave = ref<boolean>(false)

// Student Excel Import Workflow
const isUploadingSheet = ref<boolean>(false)
const isCommittingImport = ref<boolean>(false)
const currentImportJob = ref<ImportJobResponse | null>(null)
const importSummary = ref<{ imported_count: number; skipped_count: number; errors: string[] } | null>(null)

// Any student or mentor can be assigned as mentor
const mentorUsers = computed<UserItem[]>(() => users.value)

const activeRotation = computed<RotationItem | null>(() => {
	return rotations.value.find((r) => r.status === 'active') || null
})

async function fetchUsers(): Promise<void> {
	try {
		const res = await api.get<UserItem[]>('/admin/users')
		if (res.success && res.data) {
			users.value = res.data
		}
	} catch {
		// Silent error
	}
}

async function fetchRotations(): Promise<void> {
	try {
		const res = await api.get<RotationItem[]>('/admin/mentors/rotation')
		if (res.success && res.data) {
			rotations.value = res.data
		}
	} catch {
		// Silent error
	}
}

async function fetchLeaves(): Promise<void> {
	try {
		const res = await api.get<CustomLeaveItem[]>('/admin/leaves')
		if (res.success && res.data) {
			leaves.value = res.data
		}
	} catch {
		// Silent error
	}
}


async function handleUploadSheet(file: File, targetYear: string): Promise<void> {
	isUploadingSheet.value = true
	currentImportJob.value = null
	importSummary.value = null

	try {
		const formData = new FormData()
		formData.append('file', file)
		formData.append('year_batch', targetYear)

		const res = await api.upload<ImportJobResponse>('/admin/students/import-upload', formData)
		if (res.success && res.data) {
			currentImportJob.value = res.data
			notify({ color: 'success', message: 'Spreadsheet analyzed. Columns mapped with AI.' })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Failed to upload spreadsheet.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Upload error' })
	} finally {
		isUploadingSheet.value = false
	}
}

async function handleCommitImport(mapping: Record<string, number>): Promise<void> {
	if (!currentImportJob.value) return
	isCommittingImport.value = true

	try {
		const res = await api.post<{ imported_count: number; skipped_count: number; errors: string[] }>(
			'/admin/students/import-commit',
			{
				job_id: currentImportJob.value.job_id,
				column_mapping: mapping,
			}
		)

		if (res.success && res.data) {
			importSummary.value = res.data
			notify({ color: 'success', message: `Successfully committed ${res.data.imported_count} students!` })
			await fetchUsers()
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Import commit failed.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Commit error' })
	} finally {
		isCommittingImport.value = false
	}
}

async function handleScheduleMentor(payload: { user_id: number; week_start_date: string; week_end_date: string }): Promise<void> {
	isScheduling.value = true
	try {
		const res = await api.post<RotationItem>('/admin/mentors/rotation', payload)
		if (res.success && res.data) {
			rotations.value.unshift(res.data)
			notify({ color: 'success', message: 'Mentor assigned to rotation successfully.' })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Could not schedule mentor.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Scheduling error' })
	} finally {
		isScheduling.value = false
	}
}

async function handleEditRotation(payload: { id: number; user_id: number; week_start_date: string; week_end_date: string }): Promise<void> {
	try {
		const res = await api.put<RotationItem>(`/admin/mentors/rotation/${payload.id}`, {
			user_id: payload.user_id,
			week_start_date: payload.week_start_date,
			week_end_date: payload.week_end_date,
		})
		if (res.success && res.data) {
			const idx = rotations.value.findIndex((r) => r.id === payload.id)
			if (idx !== -1) rotations.value[idx] = res.data
			notify({ color: 'success', message: 'Rotation updated.' })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Could not update rotation.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Update error' })
	}
}

async function handleDeleteRotation(rotationId: number): Promise<void> {
	try {
		const res = await api.delete<{ id: number }>(`/admin/mentors/rotation/${rotationId}`)
		if (res.success) {
			rotations.value = rotations.value.filter((r) => r.id !== rotationId)
			notify({ color: 'success', message: 'Rotation deleted.' })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Could not delete rotation.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Delete error' })
	}
}

async function handleCreateUser(payload: { name: string; email: string; role: 'student' | 'mentor' | 'admin'; password: string }): Promise<void> {
	isCreatingUser.value = true
	try {
		const res = await api.post<UserItem>('/admin/users', payload)
		if (res.success && res.data) {
			users.value.unshift(res.data)
			notify({ color: 'success', message: `Account for ${res.data.name} created successfully.` })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Failed to create user.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Creation error' })
	} finally {
		isCreatingUser.value = false
	}
}

async function handleUpdateUser(userId: number, payload: { name: string; email: string; role: 'student' | 'mentor' | 'admin'; password?: string }): Promise<void> {
	isUpdatingUser.value = true
	try {
		const res = await api.put<UserItem>(`/admin/users/${userId}`, payload)
		if (res.success && res.data) {
			const idx = users.value.findIndex((u) => u.id === userId)
			if (idx !== -1) {
				users.value[idx] = res.data
			}
			notify({ color: 'success', message: `User ${res.data.name} updated successfully.` })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Failed to update user.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Update error' })
	} finally {
		isUpdatingUser.value = false
	}
}

async function handleCreateLeave(payload: { title: string; start_date: string; end_date: string; description?: string }): Promise<void> {
	isCreatingLeave.value = true
	try {
		const res = await api.post<CustomLeaveItem>('/admin/leaves', payload)
		if (res.success && res.data) {
			leaves.value.push(res.data)
			leaves.value.sort((a, b) => a.start_date.localeCompare(b.start_date))
			notify({ color: 'success', message: `Leave '${res.data.title}' scheduled.` })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Failed to create leave.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Error creating leave.' })
	} finally {
		isCreatingLeave.value = false
	}
}

async function handleDeleteLeave(leaveId: number): Promise<void> {
	isDeletingLeave.value = true
	try {
		const res = await api.delete<{ id: number }>(`/admin/leaves/${leaveId}`)
		if (res.success) {
			leaves.value = leaves.value.filter((l) => l.id !== leaveId)
			notify({ color: 'success', message: 'Leave removed.' })
		} else {
			notify({ color: 'danger', message: res.error?.message || 'Failed to remove leave.' })
		}
	} catch (err: unknown) {
		notify({ color: 'danger', message: err instanceof Error ? err.message : 'Error deleting leave.' })
	} finally {
		isDeletingLeave.value = false
	}
}

onMounted(async (): Promise<void> => {
	await Promise.all([fetchUsers(), fetchRotations(), fetchLeaves()])
	isLoading.value = false
})
</script>

<template>
	<div class="admin-page">
		<AdminHubBanner
			:activeRotation="activeRotation"
			:users="users"
			@schedule="activeTab = 'rotations'"
		/>

		<!-- Section Tabs -->
		<VaTabs v-model="activeTab" class="admin-tabs">
			<template #tabs>
				<VaTab name="users">
					<VaIcon name="people" size="small" class="tab-icon" />
					User Directory ({{ users.length }})
				</VaTab>
				<VaTab name="rotations">
					<VaIcon name="calendar_month" size="small" class="tab-icon" />
					Mentor Schedule ({{ rotations.length }})
				</VaTab>
			</template>
		</VaTabs>

		<!-- SECTION 1: USER DIRECTORY (WITH INLINE ROSTER IMPORT & USER EDITING) -->
		<UserDirectorySection
			v-if="activeTab === 'users'"
			:users="users"
			:isCreating="isCreatingUser"
			:isUpdating="isUpdatingUser"
			:isUploadingSheet="isUploadingSheet"
			:isCommittingImport="isCommittingImport"
			:importJob="currentImportJob"
			:importSummary="importSummary"
			@createUser="handleCreateUser"
			@updateUser="handleUpdateUser"
			@uploadRoster="handleUploadSheet"
			@commitRoster="handleCommitImport"
		/>

		<!-- SECTION 2: MENTOR SCHEDULE (GOOGLE CALENDAR STYLE MINI CALENDAR) -->
		<MentorScheduleSection
			v-if="activeTab === 'rotations'"
			:rotations="rotations"
			:leaves="leaves"
			:mentorUsers="mentorUsers"
			:isScheduling="isScheduling"
			:isCreatingLeave="isCreatingLeave"
			:isDeletingLeave="isDeletingLeave"
			@schedule="handleScheduleMentor"
			@editRotation="handleEditRotation"
			@deleteRotation="handleDeleteRotation"
			@createLeave="handleCreateLeave"
			@deleteLeave="handleDeleteLeave"
		/>
	</div>
</template>

<style scoped>
.admin-page {
	max-width: 1400px;
	margin: 0 auto;
	padding: 1.5rem;
	width: 100%;
}

.admin-tabs {
	margin-bottom: 1.5rem;
}

.tab-icon {
	margin-right: 0.5rem;
	vertical-align: middle;
}
</style>
