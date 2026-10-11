<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import type { MilestoneItem } from '@/types'
import { usePixelToast } from '@/components/pixel/usePixelToast'
import PixelButton from '@/components/pixel/PixelButton.vue'
import PixelCard from '@/components/pixel/PixelCard.vue'
import PixelCardContent from '@/components/pixel/PixelCardContent.vue'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'
import PixelModal from '@/components/pixel/PixelModal.vue'
import PixelInput from '@/components/pixel/PixelInput.vue'
import PixelTextarea from '@/components/pixel/PixelTextarea.vue'
import PixelSelect from '@/components/pixel/PixelSelect.vue'

const { init: notify } = usePixelToast()

const milestones = ref<MilestoneItem[]>([])
const isLoading = ref<boolean>(false)
const filterType = ref<string>('all')

// Modal states
const showCreateModal = ref<boolean>(false)
const showEditModal = ref<boolean>(false)
const showDeleteModal = ref<boolean>(false)
const isSubmitting = ref<boolean>(false)

// Active target for edit/delete
const targetMilestone = ref<MilestoneItem | null>(null)

// Form state
const formName = ref<string>('')
const formDescription = ref<string>('')
const formThresholdType = ref<'streak_days' | 'total_points' | 'problems_solved'>('total_points')
const formThresholdValue = ref<number>(100)
const formRewardType = ref<'badge' | 'points' | 'custom'>('badge')
const formIcon = ref<string>('gem_ruby')
const formPointsValue = ref<number>(50)
const formIsActive = ref<boolean>(true)

const THRESHOLD_TYPE_OPTIONS = [
	{ value: 'total_points', label: 'Total XP Accumulated' },
	{ value: 'streak_days', label: 'Consecutive Day Streak' },
	{ value: 'problems_solved', label: 'Total Problems Solved' },
]

const REWARD_TYPE_OPTIONS = [
	{ value: 'badge', label: 'Milestone Badge' },
	{ value: 'points', label: 'XP Points Bonus' },
	{ value: 'custom', label: 'Special Recognition' },
]

const POPULAR_ICONS = [
	{ name: 'bronze', label: 'Bronze' },
	{ name: 'silver', label: 'Silver' },
	{ name: 'gold', label: 'Gold' },
	{ name: 'gem_amber', label: 'Amber' },
	{ name: 'gem_emerald', label: 'Emerald' },
	{ name: 'gem_sapphire', label: 'Sapphire' },
	{ name: 'gem_ruby', label: 'Ruby' },
	{ name: 'gem_diamond', label: 'Diamond' },
	{ name: 'flame', label: 'Flame' },
	{ name: 'thunder', label: 'Thunder' },
	{ name: 'star_gold', label: 'Gold Star' },
	{ name: 'trophy', label: 'Trophy' },
	{ name: 'crown', label: 'Crown' },
	{ name: 'shield', label: 'Shield' },
	{ name: 'sword', label: 'Sword' },
	{ name: 'chest', label: 'Chest' },
	{ name: 'potion', label: 'Potion' },
	{ name: 'scroll', label: 'Scroll' },
]

const ICON_OPTIONS = POPULAR_ICONS.map((i) => ({ value: i.name, label: i.label }))

const FILTER_OPTIONS = [
	{ value: 'all', label: 'All Achievements & Badges' },
	{ value: 'total_points', label: 'XP Milestones' },
	{ value: 'streak_days', label: 'Streak Badges' },
	{ value: 'problems_solved', label: 'Problem Count Milestones' },
]

const filteredMilestones = computed<MilestoneItem[]>(() => {
	if (filterType.value === 'all') return milestones.value
	return milestones.value.filter((m) => m.threshold_type === filterType.value)
})

async function fetchMilestones(): Promise<void> {
	isLoading.value = true
	try {
		const res = await api.get<MilestoneItem[]>('/admin/achievements')
		if (res.success && res.data) {
			milestones.value = res.data
		}
	} catch {
		notify({ color: 'danger', message: 'Failed to load achievements.' })
	} finally {
		isLoading.value = false
	}
}

function openCreateModal(): void {
	formName.value = ''
	formDescription.value = ''
	formThresholdType.value = 'total_points'
	formThresholdValue.value = 500
	formRewardType.value = 'badge'
	formIcon.value = 'gem_emerald'
	formPointsValue.value = 100
	formIsActive.value = true
	showCreateModal.value = true
}

function openEditModal(m: MilestoneItem): void {
	targetMilestone.value = m
	formName.value = m.name
	formDescription.value = m.description || ''
	formThresholdType.value = m.threshold_type
	formThresholdValue.value = m.threshold_value
	formRewardType.value = m.reward_type
	formIcon.value = m.icon || 'gem_ruby'
	formPointsValue.value = m.points_value || 0
	formIsActive.value = m.is_active
	showEditModal.value = true
}

function openDeleteModal(m: MilestoneItem): void {
	targetMilestone.value = m
	showDeleteModal.value = true
}

async function handleCreateMilestone(): Promise<void> {
	if (!formName.value.trim()) {
		notify({ color: 'warning', message: 'Please enter an achievement title.' })
		return
	}
	if (formThresholdValue.value <= 0) {
		notify({ color: 'warning', message: 'Threshold requirement must be greater than 0.' })
		return
	}

	isSubmitting.value = true
	try {
		const payload = {
			name: formName.value.trim(),
			description: formDescription.value.trim(),
			threshold_type: formThresholdType.value,
			threshold_value: Number(formThresholdValue.value),
			reward_type: formRewardType.value,
			icon: formIcon.value,
			points_value: Number(formPointsValue.value) || 0,
			is_active: formIsActive.value,
		}

		const res = await api.post<MilestoneItem>('/admin/achievements', payload)
		if (res.success && res.data) {
			notify({ color: 'success', message: `Achievement '${res.data.name}' created.` })
			showCreateModal.value = false
			await fetchMilestones()
		} else {
			notify({
				color: 'danger',
				message: res.error?.message || 'Failed to create achievement.',
			})
		}
	} catch (err: unknown) {
		notify({
			color: 'danger',
			message: err instanceof Error ? err.message : 'Error creating achievement',
		})
	} finally {
		isSubmitting.value = false
	}
}

async function handleUpdateMilestone(): Promise<void> {
	if (!targetMilestone.value) return
	if (!formName.value.trim()) {
		notify({ color: 'warning', message: 'Please enter an achievement title.' })
		return
	}

	isSubmitting.value = true
	try {
		const payload = {
			name: formName.value.trim(),
			description: formDescription.value.trim(),
			threshold_type: formThresholdType.value,
			threshold_value: Number(formThresholdValue.value),
			reward_type: formRewardType.value,
			icon: formIcon.value,
			points_value: Number(formPointsValue.value) || 0,
			is_active: formIsActive.value,
		}

		const res = await api.put<MilestoneItem>(
			`/admin/achievements/${targetMilestone.value.id}`,
			payload,
		)
		if (res.success && res.data) {
			notify({ color: 'success', message: `Achievement '${res.data.name}' updated.` })
			showEditModal.value = false
			await fetchMilestones()
		} else {
			notify({
				color: 'danger',
				message: res.error?.message || 'Failed to update achievement.',
			})
		}
	} catch (err: unknown) {
		notify({
			color: 'danger',
			message: err instanceof Error ? err.message : 'Error updating achievement',
		})
	} finally {
		isSubmitting.value = false
	}
}

async function handleDeleteMilestone(): Promise<void> {
	if (!targetMilestone.value) return
	isSubmitting.value = true
	try {
		const res = await api.delete<{ id: number }>(
			`/admin/achievements/${targetMilestone.value.id}`,
		)
		if (res.success) {
			notify({ color: 'success', message: `Achievement removed successfully.` })
			showDeleteModal.value = false
			targetMilestone.value = null
			await fetchMilestones()
		} else {
			notify({
				color: 'danger',
				message: res.error?.message || 'Failed to delete achievement.',
			})
		}
	} catch (err: unknown) {
		notify({
			color: 'danger',
			message: err instanceof Error ? err.message : 'Error deleting achievement',
		})
	} finally {
		isSubmitting.value = false
	}
}

function getThresholdLabel(type: string, val: number): string {
	if (type === 'streak_days') return `${val}-Day Streak`
	if (type === 'total_points') return `${val.toLocaleString()} XP Points`
	if (type === 'problems_solved') return `${val} Problems Solved`
	return `${val}`
}

function getMetricSprite(type: string): string {
	if (type === 'streak_days') return 'flame'
	if (type === 'total_points') return 'thunder'
	if (type === 'problems_solved') return 'sword'
	return 'star_gold'
}

onMounted(async () => {
	await fetchMilestones()
})
</script>

<template>
	<div class="achievements-admin-section">
		<!-- Header banner -->
		<PixelCard class="header-card">
			<PixelCardContent class="header-content">
				<div class="header-info">
					<div class="header-title-row">
						<PixelSprite name="trophy" :scale="1.5" class="title-icon" />
						<h2 class="header-title">Achievements, Streaks & Badges</h2>
					</div>
				</div>
				<div class="header-actions">
					<PixelButton variant="primary" @click="openCreateModal">
						<PixelIcon name="plus" :size="14" class="btn-icon" />
						Add Milestone / Badge
					</PixelButton>
				</div>
			</PixelCardContent>
		</PixelCard>

		<!-- Filter Bar -->
		<div class="filter-bar">
			<div class="filter-select-wrapper">
				<PixelSelect v-model="filterType" :options="FILTER_OPTIONS" size="small" />
			</div>
			<div class="count-badge">
				<PixelBadge color="neutral">
					{{ filteredMilestones.length }}
					{{ filteredMilestones.length === 1 ? 'Milestone' : 'Milestones' }}
				</PixelBadge>
			</div>
		</div>

		<!-- Empty state -->
		<PixelCard v-if="filteredMilestones.length === 0 && !isLoading" class="empty-card">
			<PixelCardContent class="empty-content">
				<PixelSprite name="chest" :scale="2" class="empty-icon" />
				<h3 class="empty-title">No Milestones Found</h3>
				<p class="empty-desc">
					Create your first achievement or milestone badge to motivate students with
					custom rewards and XP streaks.
				</p>
				<PixelButton variant="primary" size="small" @click="openCreateModal">
					Create Achievement
				</PixelButton>
			</PixelCardContent>
		</PixelCard>

		<!-- Grid of Milestones -->
		<div v-else class="milestones-grid">
			<PixelCard
				v-for="m in filteredMilestones"
				:key="m.id"
				class="milestone-card"
				:class="{ 'milestone-card--inactive': !m.is_active }"
			>
				<PixelCardContent class="card-inner">
					<div class="card-top">
						<div class="badge-icon-box">
							<PixelSprite :name="m.icon || 'gem_ruby'" :scale="2" />
						</div>
						<div class="card-headings">
							<div class="card-title-row">
								<h4 class="card-title">{{ m.name }}</h4>
								<PixelBadge v-if="!m.is_active" color="neutral" size="small"
									>Inactive</PixelBadge
								>
							</div>
							<p class="card-desc">
								{{ m.description || 'No description provided.' }}
							</p>
						</div>
					</div>

					<div class="card-details">
						<!-- Requirement Pill -->
						<div class="detail-row">
							<span class="detail-label">Requirement:</span>
							<span class="detail-value requirement-value">
								<PixelSprite
									:name="getMetricSprite(m.threshold_type)"
									:scale="0.9"
									class="metric-icon"
								/>
								{{ getThresholdLabel(m.threshold_type, m.threshold_value) }}
							</span>
						</div>

						<!-- Reward Pill -->
						<div class="detail-row">
							<span class="detail-label">Reward:</span>
							<span class="detail-value reward-value">
								<PixelSprite name="thunder" :scale="0.9" class="metric-icon" />
								+{{ m.points_value }} Bonus XP
								<span v-if="m.reward_type === 'badge'" class="badge-tag"
									>(Badge)</span
								>
							</span>
						</div>

						<!-- Unlocks counter -->
						<div class="detail-row">
							<span class="detail-label">Earned By:</span>
							<span class="detail-value earned-value">
								<PixelIcon name="user" :size="12" class="user-icon" />
								{{ m.earned_count }}
								{{ m.earned_count === 1 ? 'student' : 'students' }}
							</span>
						</div>
					</div>

					<!-- Card Actions -->
					<div class="card-actions">
						<PixelButton variant="secondary" size="small" @click="openEditModal(m)">
							<PixelIcon name="edit" :size="12" class="btn-icon" />
							Edit
						</PixelButton>
						<PixelButton variant="danger" size="small" @click="openDeleteModal(m)">
							<PixelIcon name="trash" :size="12" class="btn-icon" />
							Delete
						</PixelButton>
					</div>
				</PixelCardContent>
			</PixelCard>
		</div>

		<!-- CREATE MODAL -->
		<PixelModal
			v-model="showCreateModal"
			title="Create New Milestone / Badge"
			ok-text="Create Achievement"
			cancel-text="Cancel"
			:loading="isSubmitting"
			max-width="640px"
			@ok="handleCreateMilestone"
			@cancel="showCreateModal = false"
		>
			<div class="form-container">
				<div class="form-row">
					<PixelInput
						v-model="formName"
						label="Achievement / Badge Name *"
						placeholder="e.g. Ruby Champion, 14-Day Code Streak"
					/>
				</div>

				<div class="form-row">
					<PixelTextarea
						v-model="formDescription"
						label="Description / Lore"
						placeholder="e.g. Awarded to persistent engineers for sustaining a two-week daily streak."
						:rows="2"
					/>
				</div>

				<div class="form-columns">
					<div class="form-col">
						<label class="form-label">Requirement Metric *</label>
						<PixelSelect
							v-model="formThresholdType"
							:options="THRESHOLD_TYPE_OPTIONS"
						/>
					</div>
					<div class="form-col">
						<PixelInput
							v-model.number="formThresholdValue"
							label="Threshold Value *"
							type="number"
							placeholder="e.g. 1000"
						/>
					</div>
				</div>

				<div class="form-columns">
					<div class="form-col">
						<label class="form-label">Reward Type</label>
						<PixelSelect v-model="formRewardType" :options="REWARD_TYPE_OPTIONS" />
					</div>
					<div class="form-col">
						<PixelInput
							v-model.number="formPointsValue"
							label="Bonus XP Reward"
							type="number"
							placeholder="e.g. 50"
						/>
					</div>
				</div>

				<!-- Sprite Icon Picker -->
				<div class="form-row">
					<label class="form-label">Badge Sprite Icon (Selected: {{ formIcon }})</label>
					<div class="icon-palette">
						<button
							v-for="ico in POPULAR_ICONS"
							:key="ico.name"
							type="button"
							class="icon-palette-btn"
							:class="{ 'icon-palette-btn--active': formIcon === ico.name }"
							:title="ico.label"
							@click="formIcon = ico.name"
						>
							<PixelSprite :name="ico.name" :scale="1.5" />
							<span class="icon-palette-label">{{ ico.label }}</span>
						</button>
					</div>
				</div>
			</div>
		</PixelModal>

		<!-- EDIT MODAL -->
		<PixelModal
			v-model="showEditModal"
			title="Edit Achievement / Badge"
			ok-text="Save Changes"
			cancel-text="Cancel"
			:loading="isSubmitting"
			max-width="640px"
			@ok="handleUpdateMilestone"
			@cancel="showEditModal = false"
		>
			<div v-if="targetMilestone" class="form-container">
				<div class="form-row">
					<PixelInput v-model="formName" label="Achievement / Badge Name *" />
				</div>

				<div class="form-row">
					<PixelTextarea v-model="formDescription" label="Description" :rows="2" />
				</div>

				<div class="form-columns">
					<div class="form-col">
						<label class="form-label">Requirement Metric *</label>
						<PixelSelect
							v-model="formThresholdType"
							:options="THRESHOLD_TYPE_OPTIONS"
						/>
					</div>
					<div class="form-col">
						<PixelInput
							v-model.number="formThresholdValue"
							label="Threshold Value *"
							type="number"
						/>
					</div>
				</div>

				<div class="form-columns">
					<div class="form-col">
						<label class="form-label">Reward Type</label>
						<PixelSelect v-model="formRewardType" :options="REWARD_TYPE_OPTIONS" />
					</div>
					<div class="form-col">
						<PixelInput
							v-model.number="formPointsValue"
							label="Bonus XP Reward"
							type="number"
						/>
					</div>
				</div>

				<!-- Sprite Icon Picker -->
				<div class="form-row">
					<label class="form-label">Badge Sprite Icon (Selected: {{ formIcon }})</label>
					<div class="icon-palette">
						<button
							v-for="ico in POPULAR_ICONS"
							:key="ico.name"
							type="button"
							class="icon-palette-btn"
							:class="{ 'icon-palette-btn--active': formIcon === ico.name }"
							:title="ico.label"
							@click="formIcon = ico.name"
						>
							<PixelSprite :name="ico.name" :scale="1.5" />
							<span class="icon-palette-label">{{ ico.label }}</span>
						</button>
					</div>
				</div>
			</div>
		</PixelModal>

		<!-- DELETE CONFIRMATION MODAL -->
		<PixelModal
			v-model="showDeleteModal"
			title="Delete Achievement"
			ok-text="Delete Achievement"
			ok-color="danger"
			cancel-text="Cancel"
			:loading="isSubmitting"
			max-width="480px"
			@ok="handleDeleteMilestone"
			@cancel="showDeleteModal = false"
		>
			<div v-if="targetMilestone" class="delete-confirm-box">
				<PixelSprite
					:name="targetMilestone.icon || 'trophy'"
					:scale="2"
					class="delete-icon"
				/>
				<p class="delete-warning">
					Are you sure you want to permanently delete the milestone
					<strong>"{{ targetMilestone.name }}"</strong>?
				</p>
				<p class="delete-subtext">
					This milestone will no longer be awarded to students upon completing
					requirements. Past awarded records will be unlinked.
				</p>
			</div>
		</PixelModal>
	</div>
</template>

<style scoped>
.achievements-admin-section {
	display: flex;
	flex-direction: column;
	gap: 1.5rem;
}

.header-card {
	background: var(--pixel-surface, #1e1e24);
	border: 2px solid var(--pixel-border, #3a3a4c);
}

.header-content {
	display: flex;
	justify-content: space-between;
	align-items: center;
	flex-wrap: wrap;
	gap: 1.5rem;
	padding: 1.25rem;
}

.header-info {
	max-width: 800px;
}

.header-title-row {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	margin-bottom: 0.5rem;
}

.title-icon {
	filter: drop-shadow(0 0 6px rgba(255, 215, 0, 0.4));
}

.header-title {
	font-family: var(--pixel-font, 'Courier New', monospace);
	font-size: 1.35rem;
	font-weight: 700;
	color: var(--pixel-text, #f0f0f5);
	margin: 0;
	letter-spacing: 0.5px;
}

.header-desc {
	font-size: 0.85rem;
	line-height: 1.45;
	color: var(--pixel-text-muted, #9ca3af);
	margin: 0;
}

.header-actions {
	display: flex;
	align-items: center;
	gap: 0.75rem;
}

.btn-icon {
	margin-right: 0.35rem;
	vertical-align: middle;
}

/* Filter bar */
.filter-bar {
	display: flex;
	justify-content: space-between;
	align-items: center;
	flex-wrap: wrap;
	gap: 1rem;
}

.filter-select-wrapper {
	min-width: 260px;
}

/* Empty state */
.empty-card {
	text-align: center;
	padding: 3rem 1.5rem;
	background: var(--pixel-surface, #1e1e24);
}

.empty-content {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 1rem;
}

.empty-title {
	font-family: var(--pixel-font, monospace);
	font-size: 1.2rem;
	color: var(--pixel-text, #f0f0f5);
	margin: 0;
}

.empty-desc {
	font-size: 0.85rem;
	color: var(--pixel-text-muted, #9ca3af);
	max-width: 460px;
	margin: 0;
}

/* Grid */
.milestones-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
	gap: 1.25rem;
}

.milestone-card {
	background: var(--pixel-surface, #1e1e24);
	border: 2px solid var(--pixel-border, #3a3a4c);
	transition:
		transform 0.15s ease,
		border-color 0.15s ease;
}

.milestone-card:hover {
	border-color: var(--pixel-primary, #6366f1);
	transform: translateY(-2px);
}

.milestone-card--inactive {
	opacity: 0.6;
}

.card-inner {
	display: flex;
	flex-direction: column;
	height: 100%;
	padding: 1.25rem;
	gap: 1rem;
}

.card-top {
	display: flex;
	gap: 1rem;
	align-items: flex-start;
}

.badge-icon-box {
	width: 52px;
	height: 52px;
	background: rgba(0, 0, 0, 0.4);
	border: 2px solid var(--pixel-border, #3a3a4c);
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
	box-shadow: inset 0 0 8px rgba(0, 0, 0, 0.6);
}

.card-headings {
	flex: 1;
	min-width: 0;
}

.card-title-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.5rem;
	margin-bottom: 0.35rem;
}

.card-title {
	font-family: var(--pixel-font, monospace);
	font-size: 1.05rem;
	font-weight: 700;
	color: var(--pixel-text, #f0f0f5);
	margin: 0;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.card-desc {
	font-size: 0.8rem;
	line-height: 1.35;
	color: var(--pixel-text-muted, #9ca3af);
	margin: 0;
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
}

.card-details {
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
	background: rgba(0, 0, 0, 0.25);
	border: 1px solid var(--pixel-border, #3a3a4c);
	padding: 0.75rem;
	font-size: 0.82rem;
}

.detail-row {
	display: flex;
	justify-content: space-between;
	align-items: center;
	gap: 0.5rem;
}

.detail-label {
	color: var(--pixel-text-muted, #9ca3af);
	font-weight: 500;
}

.detail-value {
	display: flex;
	align-items: center;
	gap: 0.35rem;
	font-weight: 600;
	color: var(--pixel-text, #f0f0f5);
}

.requirement-value {
	color: #38bdf8;
}

.reward-value {
	color: #fbbf24;
}

.badge-tag {
	font-size: 0.72rem;
	color: var(--pixel-text-muted, #9ca3af);
	margin-left: 0.25rem;
}

.earned-value {
	color: #a78bfa;
}

.metric-icon {
	vertical-align: middle;
}

.user-icon {
	opacity: 0.75;
}

.card-actions {
	display: flex;
	justify-content: flex-end;
	gap: 0.5rem;
	margin-top: auto;
	padding-top: 0.5rem;
}

/* Modal Form */
.form-container {
	display: flex;
	flex-direction: column;
	gap: 1rem;
}

.form-row {
	display: flex;
	flex-direction: column;
	gap: 0.35rem;
}

.form-columns {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 1rem;
}

.form-col {
	display: flex;
	flex-direction: column;
	gap: 0.35rem;
}

.form-label {
	font-family: var(--pixel-font, monospace);
	font-size: 0.8rem;
	color: var(--pixel-text-muted, #9ca3af);
	text-transform: uppercase;
	letter-spacing: 0.5px;
}

/* Icon Palette Picker */
.icon-palette {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(70px, 1fr));
	gap: 0.5rem;
	max-height: 180px;
	overflow-y: auto;
	background: rgba(0, 0, 0, 0.35);
	border: 1px solid var(--pixel-border, #3a3a4c);
	padding: 0.5rem;
}

.icon-palette-btn {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 0.25rem;
	padding: 0.4rem;
	background: transparent;
	border: 1px solid transparent;
	cursor: pointer;
	border-radius: 2px;
	color: var(--pixel-text-muted, #9ca3af);
	transition: all 0.1s ease;
}

.icon-palette-btn:hover {
	background: rgba(255, 255, 255, 0.05);
	border-color: var(--pixel-border, #3a3a4c);
}

.icon-palette-btn--active {
	background: rgba(99, 102, 241, 0.2);
	border-color: var(--pixel-primary, #6366f1);
	color: var(--pixel-text, #ffffff);
}

.icon-palette-label {
	font-size: 0.65rem;
	text-align: center;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	max-width: 100%;
}

/* Delete confirmation */
.delete-confirm-box {
	display: flex;
	flex-direction: column;
	align-items: center;
	text-align: center;
	gap: 0.75rem;
	padding: 1rem 0;
}

.delete-icon {
	margin-bottom: 0.5rem;
}

.delete-warning {
	font-size: 0.95rem;
	color: var(--pixel-text, #f0f0f5);
	margin: 0;
}

.delete-subtext {
	font-size: 0.8rem;
	color: var(--pixel-danger, #ef4444);
	margin: 0;
	max-width: 400px;
}
</style>
