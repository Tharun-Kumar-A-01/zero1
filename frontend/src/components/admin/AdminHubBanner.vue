<script setup lang="ts">
import type { RotationItem, UserItem } from '@/types'
import { formatIndianDate } from '@/utils/date'

const props = defineProps<{
	activeRotation: RotationItem | null
	users: UserItem[]
}>()

const emit = defineEmits<{
	(e: 'schedule'): void
}>()

function getMentorName(userId: number): string {
	const user = props.users.find((u) => u.id === userId)
	return user ? user.name : `Mentor #${userId}`
}
</script>

<template>
	<div class="admin-header-bar">
		<div>
			<h1 class="page-title">Admin Dashboard</h1>
		</div>

		<div class="active-rotation-strip">
			<div class="rotation-meta">
				<span class="strip-label">Active Week:</span>
				<VaBadge
					:text="activeRotation ? 'ACTIVE' : 'NO ACTIVE ROTATION'"
					:color="activeRotation ? 'success' : 'warning'"
				/>
				<span v-if="activeRotation" class="rotation-details">
					<strong>{{ getMentorName(activeRotation.user_id) }}</strong>
					({{ formatIndianDate(activeRotation.week_start_date) }} – {{ formatIndianDate(activeRotation.week_end_date) }})
				</span>
			</div>
			<VaButton
				size="small"
				icon="event"
				preset="secondary"
				@click="emit('schedule')"
			>
				Schedule Rotation
			</VaButton>
		</div>
	</div>
</template>

<style scoped>
.admin-header-bar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	flex-wrap: wrap;
	gap: 1rem;
	margin-bottom: 1.5rem;
	padding-bottom: 1rem;
	border-bottom: 1px solid var(--va-background-border);
}

.page-title {
	font-size: 1.5rem;
	font-weight: 700;
	color: var(--va-text-primary);
	margin: 0;
}

.active-rotation-strip {
	display: flex;
	align-items: center;
	gap: 1rem;
	padding: 0.5rem 0.875rem;
	background: var(--va-background-element);
	border: 1px solid var(--va-background-border);
	flex-wrap: wrap;
}

.rotation-meta {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	font-size: 0.875rem;
	color: var(--va-text-primary);
}

.strip-label {
	font-weight: 600;
	color: var(--va-secondary);
}

.rotation-details {
	font-size: 0.875rem;
}

.rotation-empty-note {
	color: var(--va-secondary);
	font-size: 0.8125rem;
}
</style>
