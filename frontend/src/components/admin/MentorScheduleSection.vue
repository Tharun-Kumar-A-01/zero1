<script setup lang="ts">
import { ref, computed } from 'vue'
import type { RotationItem, UserItem, CustomLeaveItem } from '@/types'
import { formatIndianDate, formatISODate } from '@/utils/date'

const props = defineProps<{
	rotations: RotationItem[]
	leaves: CustomLeaveItem[]
	mentorUsers: UserItem[]
	isScheduling: boolean
	isCreatingLeave?: boolean
	isDeletingLeave?: boolean
}>()

const emit = defineEmits<{
	(e: 'schedule', payload: { user_id: number; week_start_date: string; week_end_date: string }): void
	(e: 'editRotation', payload: { id: number; user_id: number; week_start_date: string; week_end_date: string }): void
	(e: 'deleteRotation', rotationId: number): void
	(e: 'createLeave', payload: { title: string; start_date: string; end_date: string; description?: string }): void
	(e: 'deleteLeave', leaveId: number): void
}>()

// Current Month/Year Navigation State
const calendarDate = ref<Date>(new Date())

const currentYear = computed(() => calendarDate.value.getFullYear())
const currentMonth = computed(() => calendarDate.value.getMonth()) // 0-indexed

const currentMonthYearLabel = computed(() => {
	return calendarDate.value.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
})

function prevMonth(): void {
	calendarDate.value = new Date(currentYear.value, currentMonth.value - 1, 1)
}

function nextMonth(): void {
	calendarDate.value = new Date(currentYear.value, currentMonth.value + 1, 1)
}

function goToToday(): void {
	calendarDate.value = new Date()
}

// Dialog States
const showScheduleDialog = ref<boolean>(false)
const selectedMentorId = ref<number | null>(null)
const rotationStartDate = ref<Date | null>(null)

const showLeaveDialog = ref<boolean>(false)
const leaveTitle = ref<string>('')
const leaveStartDate = ref<Date | null>(null)
const leaveEndDate = ref<Date | null>(null)
const leaveDescription = ref<string>('')

// Edit rotation state
const showEditRotationDialog = ref<boolean>(false)
const editTargetRotation = ref<RotationItem | null>(null)
const editSelectedMentorId = ref<number | null>(null)
const editStartDate = ref<Date | null>(null)

// Clicked event inspection
const inspectLeave = ref<CustomLeaveItem | null>(null)
const inspectRotation = ref<RotationItem | null>(null)

// Rotation color palette — distinct colors per mentor (not red which is for leaves)
const ROTATION_PALETTE = [
	'#154EC1', // primary blue
	'#3D9209', // success green
	'#7B2FBE', // purple
	'#D97706', // amber
	'#0E7490', // teal
	'#9D174D', // rose
	'#1D4ED8', // indigo
	'#065F46', // emerald
]

function rotationColor(userId: number): string {
	return ROTATION_PALETTE[userId % ROTATION_PALETTE.length] ?? ROTATION_PALETTE[0]!
}

// Member options for mentor assignment — only mentors can be scheduled
const mentorOptions = computed<Array<{ label: string; value: number }>>(() => {
	return props.mentorUsers
		.filter((m) => m.role === 'mentor')
		.map((m) => ({
			label: `${m.name} (${m.email})`,
			value: m.id,
		}))
})

function getMentorUser(userId: number): UserItem | undefined {
	return props.mentorUsers.find((u) => u.id === userId)
}

function getMentorName(userId: number): string {
	const user = getMentorUser(userId)
	return user ? user.name : `Mentor ID #${userId}`
}


// Compute the end date so the mentor gets exactly 6 working days (Sundays skipped)
function computeWorkingEnd(start: Date): Date {
	let d = new Date(start.getFullYear(), start.getMonth(), start.getDate())
	let count = 0
	while (count < 5) {
		d = new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1)
		if (d.getDay() !== 0) count++ // skip Sundays
	}
	return d
}

function handleSaveMentor(): void {
	if (!selectedMentorId.value || !rotationStartDate.value) return

	// Advance to Monday if admin picked a Sunday
	let start = new Date(rotationStartDate.value)
	if (start.getDay() === 0) {
		start = new Date(start.getFullYear(), start.getMonth(), start.getDate() + 1)
	}
	const end = computeWorkingEnd(start)

	emit('schedule', {
		user_id: selectedMentorId.value,
		week_start_date: formatISODate(start),
		week_end_date: formatISODate(end),
	})
	showScheduleDialog.value = false
	rotationStartDate.value = null
	selectedMentorId.value = null
}

function handleSaveLeave(): void {
	if (!leaveTitle.value.trim() || !leaveStartDate.value) return

	const startStr = formatISODate(leaveStartDate.value)
	const endStr = leaveEndDate.value ? formatISODate(leaveEndDate.value) : startStr

	emit('createLeave', {
		title: leaveTitle.value.trim(),
		start_date: startStr,
		end_date: endStr,
		description: leaveDescription.value.trim() || undefined,
	})
	showLeaveDialog.value = false
	leaveTitle.value = ''
	leaveStartDate.value = null
	leaveEndDate.value = null
	leaveDescription.value = ''
}

function handleDeleteLeaveConfirmed(leaveId: number): void {
	emit('deleteLeave', leaveId)
	inspectLeave.value = null
}

function openEditRotation(rot: RotationItem): void {
	editTargetRotation.value = rot
	editSelectedMentorId.value = rot.user_id
	editStartDate.value = new Date(rot.week_start_date)
	inspectRotation.value = null
	showEditRotationDialog.value = true
}

function handleSaveEditRotation(): void {
	if (!editTargetRotation.value || !editSelectedMentorId.value || !editStartDate.value) return
	let start = new Date(editStartDate.value)
	if (start.getDay() === 0) {
		start = new Date(start.getFullYear(), start.getMonth(), start.getDate() + 1)
	}
	const end = computeWorkingEnd(start)
	emit('editRotation', {
		id: editTargetRotation.value.id,
		user_id: editSelectedMentorId.value,
		week_start_date: formatISODate(start),
		week_end_date: formatISODate(end),
	})
	showEditRotationDialog.value = false
	editTargetRotation.value = null
	editSelectedMentorId.value = null
	editStartDate.value = null
}

function handleDeleteRotationConfirmed(rotId: number): void {
	emit('deleteRotation', rotId)
	inspectRotation.value = null
}

// Calendar Month Grid Generation
interface CalendarDay {
	date: Date
	dateStr: string
	dayNumber: number
	isCurrentMonth: boolean
	isToday: boolean
	dayOfWeek: number // 0 = Sun, 6 = Sat
	isSunday: boolean
	leaves: CustomLeaveItem[]
	rotations: RotationItem[]
}

const calendarWeeks = computed<CalendarDay[][]>(() => {
	const year = currentYear.value
	const month = currentMonth.value
	const todayStr = formatISODate(new Date())

	const firstDay = new Date(year, month, 1)
	// Sunday = 0, Monday = 1, ..., Saturday = 6
	const firstDayOffset = firstDay.getDay()

	const lastDay = new Date(year, month + 1, 0)
	const totalDaysInMonth = lastDay.getDate()
	const lastDayOffset = lastDay.getDay()
	const daysAfter = 6 - lastDayOffset

	const totalDaysToRender = firstDayOffset + totalDaysInMonth + daysAfter

	const gridStartDate = new Date(year, month, 1 - firstDayOffset)
	const allDays: CalendarDay[] = []

	for (let i = 0; i < totalDaysToRender; i++) {
		const d = new Date(gridStartDate.getFullYear(), gridStartDate.getMonth(), gridStartDate.getDate() + i)
		const dateStr = formatISODate(d)
		const isCurrentMonth = d.getMonth() === month
		const isToday = dateStr === todayStr
		const dayOfWeek = d.getDay() // 0 = Sun, 6 = Sat
		const isSunday = dayOfWeek === 0

		// Match custom department leaves
		const matchedLeaves = props.leaves.filter((l) => {
			return l.start_date <= dateStr && dateStr <= l.end_date
		})

		// A day is a leave day if it's Sunday or has any custom leave
		const isLeaveDay = isSunday || matchedLeaves.length > 0

		// Mentor rotations: only show on non-leave days
		const matchedRotations = isLeaveDay
			? []
			: props.rotations.filter((r) => {
					return r.week_start_date <= dateStr && dateStr <= r.week_end_date
				})

		allDays.push({
			date: d,
			dateStr,
			dayNumber: d.getDate(),
			isCurrentMonth,
			isToday,
			dayOfWeek,
			isSunday,
			leaves: matchedLeaves,
			rotations: matchedRotations,
		})
	}

	// Split into weeks of 7 days
	const weeks: CalendarDay[][] = []
	for (let i = 0; i < allDays.length; i += 7) {
		weeks.push(allDays.slice(i, i + 7))
	}
	return weeks
})

const weekDaysHeader = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

// Helper to determine event bar spanning / label display
// For leaves: row starts on Sun col (0) or actual leave start; ends on Sat col (6) or actual leave end
function isLeaveStart(leave: CustomLeaveItem, day: CalendarDay): boolean {
	return leave.start_date === day.dateStr || day.dayOfWeek === 0
}

function isLeaveEnd(leave: CustomLeaveItem, day: CalendarDay): boolean {
	return leave.end_date === day.dateStr || day.dayOfWeek === 6
}

// For rotations: Sunday is always suppressed.
// A cell is a rotation start if it's the start date, Monday (row start), or the day after a leave/holiday.
function isRotationStart(rot: RotationItem, day: CalendarDay): boolean {
	if (rot.week_start_date === day.dateStr || day.dayOfWeek === 1) return true
	const prev = new Date(day.date)
	prev.setDate(prev.getDate() - 1)
	const prevStr = formatISODate(prev)
	if (prevStr < rot.week_start_date || prev.getDay() === 0) return true
	return props.leaves.some((l) => l.start_date <= prevStr && prevStr <= l.end_date)
}

// A cell is a rotation end if it's the end date, Saturday (row end), or the day before a leave/holiday.
function isRotationEnd(rot: RotationItem, day: CalendarDay): boolean {
	if (rot.week_end_date === day.dateStr || day.dayOfWeek === 6) return true
	const next = new Date(day.date)
	next.setDate(next.getDate() + 1)
	const nextStr = formatISODate(next)
	if (nextStr > rot.week_end_date || next.getDay() === 0) return true
	return props.leaves.some((l) => l.start_date <= nextStr && nextStr <= l.end_date)
}
</script>

<template>
	<div class="schedule-section">
		<!-- CALENDAR TOOLBAR -->
		<VaCard class="calendar-toolbar-card">
			<VaCardContent class="toolbar-content">
				<div class="nav-controls">
					<VaButton
						preset="secondary"
						size="small"
						icon="chevron_left"
						aria-label="Previous month"
						@click="prevMonth"
					/>
					<h2 class="calendar-month-title">{{ currentMonthYearLabel }}</h2>
					<VaButton
						preset="secondary"
						size="small"
						icon="chevron_right"
						aria-label="Next month"
						@click="nextMonth"
					/>
					<VaButton
						preset="secondary"
						size="small"
						icon="calendar_today"
						@click="goToToday"
					>
						Today
					</VaButton>
				</div>

				<div class="action-buttons">
					<VaButton
						size="small"
						color="primary"
						icon="event"
						@click="showScheduleDialog = true"
					>
						Assign Mentor
					</VaButton>
					<VaButton
						size="small"
						color="danger"
						icon="event_busy"
						@click="showLeaveDialog = true"
					>
						Add Department Leave
					</VaButton>
				</div>
			</VaCardContent>
		</VaCard>

		<!-- GOOGLE CALENDAR STYLE MONTH GRID -->
		<VaCard class="calendar-grid-card">
			<!-- Weekday Column Headers -->
			<div class="calendar-header-row">
				<div
					v-for="dayName in weekDaysHeader"
					:key="dayName"
					class="calendar-header-cell"
				>
					{{ dayName }}
				</div>
			</div>

			<!-- Weeks Grid -->
			<div class="calendar-month-body">
				<div
					v-for="(week, wIdx) in calendarWeeks"
					:key="wIdx"
					class="calendar-week-row"
				>
					<div
						v-for="day in week"
						:key="day.dateStr"
						class="calendar-day-cell"
						:class="{
							'is-other-month': !day.isCurrentMonth,
							'is-today': day.isToday,
							'is-leave-day': day.isSunday || day.leaves.length > 0,
						}"
					>
						<!-- Day Header -->
						<div class="day-number-wrapper">
							<span
								class="day-number"
								:class="{ 'today-badge': day.isToday }"
							>
								{{ day.dayNumber }}
							</span>
						</div>

						<!-- Events in this Day -->
						<div class="day-events-stack">
							<!-- 1. Custom Department Leaves (Red Bar) -->
							<div
								v-for="leave in day.leaves"
								:key="leave.id"
								class="event-bar leave-bar"
								:class="{
									'is-start': isLeaveStart(leave, day),
									'is-end': isLeaveEnd(leave, day),
								}"
								:title="`${leave.title} (${formatIndianDate(leave.start_date)} – ${formatIndianDate(leave.end_date)})`"
								@click="inspectLeave = leave"
							>
								<template v-if="isLeaveStart(leave, day)">
									<VaIcon name="beach_access" size="13px" class="event-icon" />
									<span class="event-label">{{ leave.title }}</span>
								</template>
								<span v-else class="event-continuation-dot"></span>
							</div>

							<!-- 2. Mentor Rotations (color-coded per mentor) -->
							<div
								v-for="rot in day.rotations"
								:key="rot.id"
								class="event-bar rotation-bar"
								:class="{
									'is-start': isRotationStart(rot, day),
									'is-end': isRotationEnd(rot, day),
								}"
								:style="{ backgroundColor: rotationColor(rot.user_id) }"
								:title="`${getMentorName(rot.user_id)} (${formatIndianDate(rot.week_start_date)} – ${formatIndianDate(rot.week_end_date)})`"
								@click="inspectRotation = rot"
							>
								<template v-if="isRotationStart(rot, day)">
									<VaIcon name="school" size="13px" class="event-icon" />
									<span class="event-label">{{ getMentorName(rot.user_id) }}</span>
								</template>
								<span v-else class="event-continuation-dot"></span>
							</div>
						</div>
					</div>
				</div>
			</div>
		</VaCard>

		<!-- BOTTOM SUMMARY SECTION: LIST OF LEAVES & ROTATIONS -->
		<div class="summary-columns">
			<!-- Department Leaves Card -->
			<VaCard class="summary-card">
				<VaCardTitle class="summary-title">
					<VaIcon name="event_busy" color="danger" class="mr-2" />
					Department Leaves & Holidays ({{ leaves.length }})
				</VaCardTitle>
				<VaCardContent>
					<div v-if="leaves.length > 0" class="items-list">
						<div
							v-for="leave in leaves"
							:key="leave.id"
							class="list-item-row"
						>
							<div class="item-info">
								<span class="item-title">{{ leave.title }}</span>
								<span class="item-dates">
									<VaIcon name="date_range" size="small" />
									{{ formatIndianDate(leave.start_date) }} – {{ formatIndianDate(leave.end_date) }}
								</span>
								<p v-if="leave.description" class="item-desc">{{ leave.description }}</p>
							</div>
							<VaButton
								preset="plain"
								icon="delete"
								color="danger"
								size="small"
								aria-label="Remove leave"
								@click="emit('deleteLeave', leave.id)"
							/>
						</div>
					</div>
					<div v-else class="empty-state-text">
						No department leaves or holidays scheduled.
					</div>
				</VaCardContent>
			</VaCard>

			<!-- Active & Upcoming Rotations Card -->
			<VaCard class="summary-card">
				<VaCardTitle class="summary-title">
					<VaIcon name="school" color="primary" class="mr-2" />
					Mentor Rotations ({{ rotations.length }})
				</VaCardTitle>
				<VaCardContent>
					<div v-if="rotations.length > 0" class="items-list">
						<div
							v-for="rot in [...rotations].sort((a, b) => { const o = {active:0, upcoming:1, completed:2, cancelled:3}; const so = (o[a.status]??9)-(o[b.status]??9); return so !== 0 ? so : a.week_start_date.localeCompare(b.week_start_date) })"
							:key="rot.id"
							class="list-item-row"
						>
							<div class="item-info">
								<div class="mentor-row-head">
									<span
										class="rotation-color-dot"
										:style="{ backgroundColor: rotationColor(rot.user_id) }"
									/>
									<span class="item-title">{{ getMentorName(rot.user_id) }}</span>
									<VaBadge
										:color="rot.status === 'active' ? 'success' : rot.status === 'upcoming' ? 'info' : 'secondary'"
										:text="rot.status.toUpperCase()"
									/>
								</div>
								<span class="item-dates">
									<VaIcon name="calendar_today" size="small" />
									{{ formatIndianDate(rot.week_start_date) }} – {{ formatIndianDate(rot.week_end_date) }}
								</span>
							</div>
						</div>
					</div>
					<div v-else class="empty-state-text">
						No mentor rotations scheduled yet.
					</div>
				</VaCardContent>
			</VaCard>
		</div>

		<!-- MODAL 1: ASSIGN MENTOR -->
		<VaModal
			v-model="showScheduleDialog"
			title="Assign Mentor Rotation"
			ok-text="Assign Schedule"
			cancel-text="Cancel"
			:loading="isScheduling"
			@ok="handleSaveMentor"
		>
			<VaForm class="dialog-form">
				<VaSelect
					v-model="selectedMentorId"
					:options="mentorOptions"
					label="Select Mentor"
					value-by="value"
					text-by="label"
					required
				/>

				<VaDateInput
					v-model="rotationStartDate"
					label="Week Start Date (Monday recommended)"
					placeholder="dd/mm/yyyy"
					clearable
					required
				/>
				<p class="form-hint">
					<VaIcon name="info" size="13px" />
					End date auto-computed as start + 5 days (Mon – Sat). Sundays are skipped automatically.
				</p>
			</VaForm>
		</VaModal>

		<!-- MODAL 2: ADD DEPARTMENT LEAVE -->
		<VaModal
			v-model="showLeaveDialog"
			title="Add Department Leave / Holiday"
			ok-text="Schedule Leave"
			cancel-text="Cancel"
			:loading="isCreatingLeave"
			@ok="handleSaveLeave"
		>
			<VaForm class="dialog-form">
				<VaInput
					v-model="leaveTitle"
					label="Holiday / Leave Title"
					placeholder="e.g. Diwali Vacation, Dussehra"
					required
				/>

				<VaDateInput
					v-model="leaveStartDate"
					label="Date (or Start Date)"
					placeholder="dd/mm/yyyy"
					clearable
					required
				/>

				<VaDateInput
					v-model="leaveEndDate"
					label="End Date (optional — leave blank for single day)"
					placeholder="dd/mm/yyyy"
					clearable
				/>

				<VaTextarea
					v-model="leaveDescription"
					label="Description (Optional)"
					placeholder="Additional details regarding this leave"
					:rows="2"
				/>
			</VaForm>
		</VaModal>

		<!-- MODAL 3: LEAVE DETAILS & DELETE -->
		<VaModal
			v-if="inspectLeave"
			:model-value="!!inspectLeave"
			title="Department Leave Details"
			hide-default-actions
			@update:model-value="inspectLeave = null"
		>
			<div class="inspect-dialog-body">
				<div class="inspect-field">
					<span class="field-label">Title</span>
					<span class="field-value">{{ inspectLeave.title }}</span>
				</div>
				<div class="inspect-field">
					<span class="field-label">Date Range</span>
					<span class="field-value">
						{{ formatIndianDate(inspectLeave.start_date) }} – {{ formatIndianDate(inspectLeave.end_date) }}
					</span>
				</div>
				<div v-if="inspectLeave.description" class="inspect-field">
					<span class="field-label">Description</span>
					<span class="field-value">{{ inspectLeave.description }}</span>
				</div>

				<div class="inspect-actions">
					<VaButton
						preset="secondary"
						@click="inspectLeave = null"
					>
						Close
					</VaButton>
					<VaButton
						color="danger"
						icon="delete"
						@click="handleDeleteLeaveConfirmed(inspectLeave.id)"
					>
						Delete Leave
					</VaButton>
				</div>
			</div>
		</VaModal>

		<!-- MODAL 4: ROTATION DETAILS -->
		<VaModal
			v-if="inspectRotation"
			:model-value="!!inspectRotation"
			title="Mentor Rotation Details"
			hide-default-actions
			@update:model-value="inspectRotation = null"
		>
			<div class="inspect-dialog-body">
				<div class="inspect-field">
					<span class="field-label">Mentor</span>
					<span class="field-value">{{ getMentorName(inspectRotation.user_id) }}</span>
				</div>
				<div class="inspect-field">
					<span class="field-label">Status</span>
					<VaBadge
						:color="inspectRotation.status === 'active' ? 'success' : inspectRotation.status === 'upcoming' ? 'info' : 'secondary'"
						:text="inspectRotation.status.toUpperCase()"
					/>
				</div>
				<div class="inspect-field">
					<span class="field-label">Rotation Week</span>
					<span class="field-value">
						{{ formatIndianDate(inspectRotation.week_start_date) }} – {{ formatIndianDate(inspectRotation.week_end_date) }}
					</span>
				</div>

				<div class="inspect-actions">
					<VaButton
						preset="secondary"
						@click="inspectRotation = null"
					>
						Close
					</VaButton>
					<VaButton
						preset="secondary"
						icon="edit"
						@click="openEditRotation(inspectRotation)"
					>
						Edit
					</VaButton>
					<VaButton
						color="danger"
						icon="delete"
						@click="handleDeleteRotationConfirmed(inspectRotation.id)"
					>
						Delete
					</VaButton>
				</div>
			</div>
		</VaModal>

		<!-- MODAL 5: EDIT ROTATION -->
		<VaModal
			v-model="showEditRotationDialog"
			title="Edit Mentor Rotation"
			ok-text="Save Changes"
			cancel-text="Cancel"
			@ok="handleSaveEditRotation"
		>
			<VaForm class="dialog-form">
				<VaSelect
					v-model="editSelectedMentorId"
					:options="mentorOptions"
					label="Select Mentor"
					value-by="value"
					text-by="label"
					required
				/>
				<VaDateInput
					v-model="editStartDate"
					label="New Start Date"
					placeholder="dd/mm/yyyy"
					clearable
					required
				/>
				<p class="form-hint">
					<VaIcon name="info" size="13px" />
					End date auto-computed as 6 working days from start.
				</p>
			</VaForm>
		</VaModal>
	</div>
</template>

<style scoped>
:deep(.va-card__inner) {
	overflow: visible !important;
}

.schedule-section {
	display: flex;
	flex-direction: column;
	gap: 1.5rem;
}

/* CALENDAR TOOLBAR */
.calendar-toolbar-card {
	border: 1px solid var(--va-background-border);
}

.toolbar-content {
	display: flex;
	justify-content: space-between;
	align-items: center;
	flex-wrap: wrap;
	gap: 1rem;
	padding: 1rem 1.25rem;
}

.nav-controls {
	display: flex;
	align-items: center;
	gap: 1.25rem;
	flex-wrap: wrap;
}

.calendar-month-title {
	margin: 0;
	font-size: 1.35rem;
	font-weight: 700;
	color: var(--va-text-primary);
	min-width: 170px;
}

.nav-btn-group {
	display: flex;
	align-items: center;
	gap: 0.35rem;
}

.action-buttons {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	flex-wrap: wrap;
}

/* CALENDAR GRID */
.calendar-grid-card {
	border: 1px solid var(--va-background-border);
	overflow: visible;
	position: relative;
	z-index: 0;
	isolation: isolate;
}

.calendar-header-row {
	display: grid;
	grid-template-columns: repeat(7, minmax(0, 1fr));
	border-bottom: 1px solid var(--va-background-border);
	background-color: var(--va-background-element);
}

.calendar-header-cell {
	padding: 0.65rem 0.5rem;
	text-align: center;
	font-size: 0.8rem;
	font-weight: 700;
	color: var(--va-text-secondary);
	text-transform: uppercase;
	letter-spacing: 0.05em;
}

.calendar-month-body {
	display: flex;
	flex-direction: column;
	overflow: visible;
}

.calendar-week-row {
	display: grid;
	grid-template-columns: repeat(7, minmax(0, 1fr));
	border-bottom: 1px solid var(--va-background-border);
	overflow: visible;
	position: relative;
}

.calendar-week-row:last-child {
	border-bottom: none;
}

.calendar-day-cell {
	min-height: 105px;
	min-width: 0;
	border-right: 1px solid var(--va-background-border);
	display: flex;
	flex-direction: column;
	background-color: var(--va-background-primary);
	position: relative;
	transition: background-color 0.15s ease;
}

.calendar-day-cell:last-child {
	border-right: none;
}

.calendar-day-cell.is-other-month {
	background-color: var(--va-background-element);
	opacity: 0.6;
}

.calendar-day-cell.is-today {
	background-color: rgba(21, 78, 193, 0.04);
}

.calendar-day-cell.is-leave-day {
	background-color: rgba(228, 34, 34, 0.07);
}

.day-number-wrapper {
	display: flex;
	justify-content: flex-end;
	padding: 0.35rem 0.5rem;
}

.day-number {
	font-size: 0.78rem;
	font-weight: 600;
	color: var(--va-text-primary);
	min-width: 22px;
	height: 22px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.today-badge {
	background-color: var(--va-primary);
	color: #ffffff !important;
	border-radius: 50%;
	font-weight: 700;
}

/* EVENT BARS (SPANNING GOOGLE CALENDAR STYLE) */
.day-events-stack {
	display: flex;
	flex-direction: column;
	gap: 3px;
	width: 100%;
	overflow: visible;
	position: relative;
}

.event-bar {
	height: 22px;
	display: flex;
	align-items: center;
	gap: 4px;
	padding: 0 4px;
	font-size: 0.72rem;
	font-weight: 600;
	color: #ffffff;
	cursor: pointer;
	white-space: nowrap;
	overflow: visible;
	user-select: none;
	transition: opacity 0.15s ease;
	margin: 0;
	border-radius: 0;
	position: relative;
}

.event-bar:hover {
	opacity: 0.88;
}

.event-bar.is-start {
	border-top-left-radius: 4px;
	border-bottom-left-radius: 4px;
	margin-left: 3px;
	padding-left: 6px;
}

.event-bar.is-end {
	border-top-right-radius: 4px;
	border-bottom-right-radius: 4px;
	margin-right: 3px;
	padding-right: 6px;
}

.leave-bar {
	background-color: var(--va-danger);
}

.rotation-bar {
	background-color: var(--va-primary);
}

.event-icon {
	flex-shrink: 0;
}

.event-label {
	white-space: nowrap;
	overflow: visible;
	position: relative;
	pointer-events: none;
}

.event-continuation-dot {
	display: inline-block;
	width: 100%;
	height: 100%;
}

/* BOTTOM SUMMARY SECTION */
.summary-columns {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
	gap: 1.25rem;
}

.summary-card {
	border: 1px solid var(--va-background-border);
}

.summary-title {
	font-size: 1rem;
	font-weight: 700;
	display: flex;
	align-items: center;
	gap: 0.5rem;
}

.items-list {
	display: flex;
	flex-direction: column;
	gap: 0.75rem;
}

.list-item-row {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	padding: 0.75rem 1rem;
	background-color: var(--va-background-element);
	border: 1px solid var(--va-background-border);
	border-radius: 4px;
	gap: 0.75rem;
}

.item-info {
	display: flex;
	flex-direction: column;
	gap: 0.25rem;
	flex: 1;
}

.item-title {
	font-weight: 700;
	font-size: 0.92rem;
	color: var(--va-text-primary);
}

.rotation-color-dot {
	display: inline-block;
	width: 10px;
	height: 10px;
	border-radius: 50%;
	flex-shrink: 0;
}

.mentor-row-head {
	display: flex;
	align-items: center;
	gap: 0.75rem;
}

.item-dates {
	display: flex;
	align-items: center;
	gap: 0.35rem;
	font-size: 0.78rem;
	color: var(--va-text-secondary);
}

.item-desc {
	margin: 0.25rem 0 0;
	font-size: 0.78rem;
	color: var(--va-text-secondary);
}

.empty-state-text {
	text-align: center;
	padding: 1.5rem 1rem;
	font-size: 0.85rem;
	color: var(--va-text-secondary);
}

/* MODALS */
.dialog-form {
	display: flex;
	flex-direction: column;
	gap: 1rem;
	padding: 0.5rem 0;
}

.form-hint {
	margin: -0.5rem 0 0;
	display: flex;
	align-items: flex-start;
	gap: 0.35rem;
	font-size: 0.77rem;
	color: var(--va-text-secondary);
	line-height: 1.4;
}

.inspect-dialog-body {
	display: flex;
	flex-direction: column;
	gap: 1rem;
	padding: 0.5rem 0;
}

.inspect-field {
	display: flex;
	flex-direction: column;
	gap: 0.25rem;
}

.field-label {
	font-size: 0.75rem;
	font-weight: 600;
	color: var(--va-text-secondary);
	text-transform: uppercase;
}

.field-value {
	font-size: 0.95rem;
	font-weight: 600;
	color: var(--va-text-primary);
}

.inspect-actions {
	display: flex;
	justify-content: flex-end;
	gap: 0.75rem;
	margin-top: 1rem;
}
</style>
