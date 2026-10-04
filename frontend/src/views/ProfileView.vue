<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import type { ProgressData, LeaderboardEntry } from '@/types'
import XpStarBadge from '@/components/common/XpStarBadge.vue'
import BadgesShowcase from '@/components/student/BadgesShowcase.vue'
import CohortStandings from '@/components/student/CohortStandings.vue'

const authStore = useAuthStore()

const isLoading = ref<boolean>(true)
const progress = ref<ProgressData | null>(null)
const leaderboard = ref<LeaderboardEntry[]>([])

const user = computed(() => authStore.user)
const streakCount = computed<number>(() => progress.value?.current_streak ?? user.value?.current_streak ?? 0)
const totalPoints = computed<number>(() => progress.value?.total_points ?? user.value?.total_points ?? 0)

const currentTier = computed<string>(() => {
	const pts = totalPoints.value
	if (pts >= 1000) return 'Master Coder'
	if (pts >= 500) return 'Gold Apprentice'
	if (pts >= 200) return 'Silver Solver'
	return 'Bronze Explorer'
})

const tierProgressPercent = computed<number>(() => {
	const pts = totalPoints.value
	if (pts >= 1000) return 100
	if (pts >= 500) return Math.min(100, Math.round(((pts - 500) / 500) * 100))
	if (pts >= 200) return Math.min(100, Math.round(((pts - 200) / 300) * 100))
	return Math.min(100, Math.round((pts / 200) * 100))
})

// Generate the 7 days of the current week (Sat, Sun, Mon, Tue, Wed, Thu, Fri) matching UserProfileModal
const weekDays = computed(() => {
	const names = ['Sat', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri']
	const todayIndex = new Date().getDay()
	const mapToIdx = (d: number) => (d === 6 ? 0 : d + 1)
	const currentIdx = mapToIdx(todayIndex)

	return names.map((name, i) => {
		const isWeekend = i === 0 || i === 1
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

async function fetchProfileData(): Promise<void> {
	if (authStore.userRole === 'student') {
		try {
			const [progRes, leadRes] = await Promise.all([
				api.get<ProgressData>('/student/progress'),
				api.get<LeaderboardEntry[]>('/student/leaderboard'),
			])
			if (progRes.success && progRes.data) {
				progress.value = progRes.data
			}
			if (leadRes.success && leadRes.data) {
				leaderboard.value = leadRes.data
			}
		} catch {
			// Silent error
		}
	}
	isLoading.value = false
}

onMounted(() => {
	fetchProfileData()
})
</script>

<template>
	<div class="profile-page">
		<div class="profile-layout">
			<!-- Left Column: User Card, Streak Showcase, Tier Progression -->
			<div class="profile-main-col">
				<!-- User Info Header Card -->
				<VaCard class="user-header-card">
					<VaCardContent>
						<div class="user-header-row">
							<VaAvatar size="large" color="primary" class="profile-avatar">
								{{ user?.name ? user.name.charAt(0).toUpperCase() : 'U' }}
							</VaAvatar>

							<div class="user-meta-info">
								<div class="name-badge-row">
									<h2 class="profile-name">{{ user?.name }}</h2>
									<VaBadge
										:text="user?.role === 'admin' ? 'SYSTEM ADMINISTRATOR' : (user?.role || '').toUpperCase()"
										:color="user?.role === 'admin' ? 'danger' : user?.role === 'mentor' ? 'warning' : 'primary'"
									/>
								</div>
								<p class="profile-email">{{ user?.email }}</p>

								<div class="meta-tags-row">
									<VaBadge
										v-if="user?.year_batch"
										:text="user.year_batch"
										color="backgroundElement"
									/>
									<VaBadge
										v-if="user?.department"
										:text="user.department"
										color="backgroundElement"
									/>
									<VaBadge
										v-if="user?.roll_number"
										:text="user.roll_number"
										color="backgroundElement"
									/>
									<XpStarBadge :points="totalPoints" size="small" />
								</div>
							</div>
						</div>
					</VaCardContent>
				</VaCard>

				<!-- Streak Showcase Box (from UserProfileModal layout) -->
				<VaCard class="streak-box-card" outlined>
					<VaCardTitle class="section-card-title">
						<VaIcon name="local_fire_department" color="warning" />
						<span>Daily Consistency & Streak</span>
					</VaCardTitle>
					<VaCardContent>
						<div class="streak-top-row">
							<span class="streak-number">{{ streakCount }}</span>
							<div class="streak-flame-group">
								<VaIcon name="local_fire_department" size="40px" color="warning" />
								<span class="streak-label">Days Active Streak</span>
								<span v-if="progress?.longest_streak" class="streak-sub">
									Personal best: {{ progress.longest_streak }} days
								</span>
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

				<!-- Tier Level Progression -->
				<VaCard class="tier-card" outlined>
					<VaCardTitle class="section-card-title">
						<VaIcon name="military_tech" color="primary" />
						<span>Skill Tier Progression</span>
					</VaCardTitle>
					<VaCardContent>
						<div class="tier-labels">
							<span class="tier-name">{{ currentTier }}</span>
							<XpStarBadge :points="totalPoints" size="small" />
						</div>
						<VaProgressBar
							:model-value="tierProgressPercent"
							:show-percent="false"
							class="tier-progress-bar"
						/>
						<span class="tier-subtext">Earn points daily by solving assigned questions to unlock next tier</span>
					</VaCardContent>
				</VaCard>
			</div>

			<!-- Right Column: Milestones & Top Peers (Batch) -->
			<div class="profile-side-col">
				<BadgesShowcase :badges="progress?.badges || []" />
				<CohortStandings :leaderboard="leaderboard" :currentUserId="user?.id" />
			</div>
		</div>
	</div>
</template>

<style scoped>
.profile-page {
	max-width: 1400px;
	margin: 0 auto;
	padding: 1.5rem;
	width: 100%;
}

.profile-layout {
	display: grid;
	grid-template-columns: 1fr 380px;
	gap: 1.5rem;
}

@media (max-width: 1024px) {
	.profile-layout {
		grid-template-columns: 1fr;
	}
}

.profile-main-col {
	display: flex;
	flex-direction: column;
	gap: 1.25rem;
}

.profile-side-col {
	display: flex;
	flex-direction: column;
	gap: 1.25rem;
}

.user-header-card {
	border: 1px solid var(--va-background-border);
}

.user-header-row {
	display: flex;
	align-items: center;
	gap: 1.25rem;
}

.profile-avatar {
	font-size: 1.75rem;
	font-weight: 700;
	flex-shrink: 0;
	width: 72px;
	height: 72px;
}

.user-meta-info {
	display: flex;
	flex-direction: column;
	gap: 0.35rem;
	flex-grow: 1;
}

.name-badge-row {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	flex-wrap: wrap;
}

.profile-name {
	font-size: 1.4rem;
	font-weight: 800;
	margin: 0;
	color: var(--va-text-primary);
}

.profile-email {
	font-size: 0.9rem;
	color: var(--va-text-secondary);
	margin: 0;
}

.meta-tags-row {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	flex-wrap: wrap;
	margin-top: 0.25rem;
}

.section-card-title {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	font-weight: 700;
	font-size: 1.05rem;
}

.streak-box-card {
	border: 1px solid var(--va-background-border);
}

.streak-top-row {
	display: flex;
	align-items: center;
	gap: 1rem;
	margin-bottom: 0.5rem;
}

.streak-number {
	font-size: 3rem;
	font-weight: 800;
	color: var(--va-text-primary);
	line-height: 1;
}

.streak-flame-group {
	display: flex;
	flex-direction: column;
}

.streak-label {
	font-weight: 700;
	font-size: 1.1rem;
	color: var(--va-text-primary);
}

.streak-sub {
	font-size: 0.8rem;
	color: var(--va-text-secondary);
}

.streak-divider {
	margin: 1rem 0;
}

.days-row {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 0.5rem 0.25rem;
}

.day-col {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 0.4rem;
}

.day-circle {
	width: 38px;
	height: 38px;
	border-radius: 50%;
	border: 2px solid var(--va-background-border);
	display: flex;
	align-items: center;
	justify-content: center;
	background: var(--va-background-secondary);
	transition: all 0.2s ease;
}

.day-circle.is-solved {
	background: var(--va-success);
	border-color: var(--va-success);
}

.day-circle.is-today:not(.is-solved) {
	border-color: var(--va-primary);
	border-width: 2px;
}

.day-circle.is-weekend {
	opacity: 0.5;
}

.day-name {
	font-size: 0.8rem;
	font-weight: 500;
	color: var(--va-text-secondary);
}

.day-name.highlight {
	color: var(--va-primary);
	font-weight: 700;
}

.tier-card {
	border: 1px solid var(--va-background-border);
}

.tier-labels {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 0.65rem;
}

.tier-name {
	font-weight: 700;
	font-size: 1.05rem;
	color: var(--va-text-primary);
}

.tier-progress-bar {
	margin-bottom: 0.5rem;
}

.tier-subtext {
	font-size: 0.8rem;
	color: var(--va-text-secondary);
}
</style>
