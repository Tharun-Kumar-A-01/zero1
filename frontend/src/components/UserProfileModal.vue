<script setup lang="ts">
import { computed } from 'vue'
import XpStarBadge from '@/components/common/XpStarBadge.vue'

const props = defineProps<{
	modelValue: boolean
	user: {
		id?: number
		name: string
		email: string
		role: string
		current_streak?: number
		total_points?: number
		roll_number?: string | null
		year_batch?: string | null
		section?: string | null
	} | null
}>()

const emit = defineEmits<{
	(e: 'update:modelValue', val: boolean): void
}>()

const streakCount = computed<number>(() => props.user?.current_streak ?? 0)

// Generate the 7 days of the current week (Sat, Sun, Mon, Tue, Wed, Thu, Fri)
const weekDays = computed(() => {
	const names = ['Sat', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri']
	const todayIndex = new Date().getDay() // 0 is Sun, 6 is Sat
	// Map JS day (0=Sun, 1=Mon, ..., 6=Sat) to index in [Sat, Sun, Mon, Tue, Wed, Thu, Fri]
	// Sat -> 0, Sun -> 1, Mon -> 2, Tue -> 3, Wed -> 4, Thu -> 5, Fri -> 6
	const mapToIdx = (d: number) => (d === 6 ? 0 : d + 1)
	const currentIdx = mapToIdx(todayIndex)

	return names.map((name, i) => {
		const isWeekend = i === 0 || i === 1 // Sat, Sun
		const isSolved = streakCount.value > 0 && i <= currentIdx && !isWeekend
		const isCurrentDay = i === currentIdx
		return {
			name,
			isWeekend,
			isSolved,
			isCurrentDay,
		}
	})
})
</script>

<template>
	<VaModal
		:model-value="modelValue"
		hide-default-actions
		title="User Profile"
		@update:model-value="emit('update:modelValue', $event)"
	>
		<div v-if="user" class="profile-container">
			<!-- User Header Information -->
			<div class="user-header-card">
				<VaAvatar size="large" color="primary" class="profile-avatar">
					{{ user.name.charAt(0).toUpperCase() }}
				</VaAvatar>
				<div class="profile-meta">
					<h3 class="profile-name">{{ user.name }}</h3>
					<span class="profile-email">{{ user.email }}</span>
					<div class="profile-badges">
						<VaBadge
							:text="user.role === 'admin' ? 'SYSTEM ADMINISTRATOR' : user.role.toUpperCase()"
							:color="user.role === 'admin' ? 'danger' : user.role === 'mentor' ? 'warning' : 'primary'"
						/>
						<VaBadge
							v-if="user.roll_number"
							:text="user.roll_number"
							color="backgroundElement"
						/>
						<VaBadge
							v-if="user.year_batch"
							:text="`Batch ${user.year_batch}`"
							color="backgroundElement"
						/>
						<XpStarBadge
							v-if="user.total_points !== undefined"
							:points="user.total_points ?? 0"
							size="small"
						/>
					</div>
				</div>
			</div>

			<!-- Streak Showcase Box matching user reference mockup -->
			<VaCard class="streak-box-card" outlined>
				<VaCardContent>
					<div class="streak-top-row">
						<span class="streak-number">{{ streakCount }}</span>
						<div class="streak-flame-group">
							<VaIcon name="local_fire_department" size="36px" color="warning" />
							<span class="streak-label">Current streak</span>
						</div>
					</div>

					<VaDivider class="streak-divider" />

					<!-- 7 Days Circles Row -->
					<div class="days-row">
						<div
							v-for="(day, idx) in weekDays"
							:key="idx"
							class="day-col"
						>
							<div
								class="day-circle"
								:class="{
									'is-weekend': day.isWeekend,
									'is-solved': day.isSolved,
									'is-today': day.isCurrentDay,
								}"
							>
								<VaIcon
									v-if="day.isSolved"
									name="check"
									size="small"
									color="textInverted"
								/>
							</div>
							<span class="day-name" :class="{ 'highlight': day.isCurrentDay }">
								{{ day.name }}
							</span>
						</div>
					</div>
				</VaCardContent>
			</VaCard>

			<div class="profile-actions">
				<VaButton preset="secondary" @click="emit('update:modelValue', false)">
					Close
				</VaButton>
			</div>
		</div>
	</VaModal>
</template>

<style scoped>
.profile-container {
	display: flex;
	flex-direction: column;
	gap: 1.25rem;
	padding-top: 0.5rem;
}

.user-header-card {
	display: flex;
	align-items: center;
	gap: 1rem;
}

.profile-avatar {
	font-size: 1.5rem;
	font-weight: 700;
}

.profile-meta {
	display: flex;
	flex-direction: column;
	gap: 0.25rem;
}

.profile-name {
	font-size: 1.25rem;
	font-weight: 700;
	color: var(--va-text-primary);
	margin: 0;
}

.profile-email {
	font-size: 0.875rem;
	color: var(--va-secondary);
}

.profile-badges {
	display: flex;
	gap: 0.5rem;
	flex-wrap: wrap;
	margin-top: 0.25rem;
}

.streak-box-card {
	background: var(--va-background-secondary);
	border: 1px solid var(--va-background-border);
}

.streak-top-row {
	display: flex;
	align-items: center;
	gap: 0.75rem;
}

.streak-number {
	font-size: 4rem;
	font-weight: 800;
	line-height: 1;
	color: var(--va-text-primary);
}

.streak-flame-group {
	display: flex;
	flex-direction: column;
	justify-content: center;
	align-items: flex-start;
}

.streak-label {
	font-size: 0.875rem;
	font-weight: 600;
	color: var(--va-text-primary);
	line-height: 1.1;
}

.streak-divider {
	margin: 1rem 0;
}

.days-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0 0.5rem;
}

.day-col {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 0.5rem;
}

.day-circle {
	width: 32px;
	height: 32px;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	border: 2px solid var(--va-secondary);
	background: transparent;
}

.day-circle.is-weekend {
	border-style: dotted;
	border-color: var(--va-secondary);
	opacity: 0.7;
}

.day-circle.is-solved {
	background: var(--va-text-primary);
	border-color: var(--va-text-primary);
}

.day-name {
	font-size: 0.8125rem;
	font-weight: 600;
	color: var(--va-text-primary);
}

.day-name.highlight {
	color: var(--va-primary);
}

.profile-actions {
	display: flex;
	justify-content: flex-end;
}
</style>
