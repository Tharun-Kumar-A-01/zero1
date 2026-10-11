<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import type { ProgressData, LeaderboardEntry } from '@/types'
import BadgesShowcase from '@/components/student/BadgesShowcase.vue'
import CohortStandings from '@/components/student/CohortStandings.vue'
import PixelCard from '@/components/pixel/PixelCard.vue'
import PixelCardTitle from '@/components/pixel/PixelCardTitle.vue'
import PixelCardContent from '@/components/pixel/PixelCardContent.vue'
import PixelAvatar from '@/components/pixel/PixelAvatar.vue'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelButton from '@/components/pixel/PixelButton.vue'
import PixelProgressBar from '@/components/pixel/PixelProgressBar.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'
import AvatarPickerModal from '@/components/common/AvatarPickerModal.vue'

const router = useRouter()
const authStore = useAuthStore()

const showAvatarPicker = ref<boolean>(false)
const isLoading = ref<boolean>(true)
const progress = ref<ProgressData | null>(null)
const leaderboard = ref<LeaderboardEntry[]>([])

const user = computed(() => authStore.user)
const streakCount = computed<number>(
	() => progress.value?.current_streak ?? user.value?.current_streak ?? 0,
)
const totalPoints = computed<number>(
	() => progress.value?.total_points ?? user.value?.total_points ?? 0,
)

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

// Check user rank in leaderboard (1 = gold, 2 = silver, 3 = bronze)
const userRank = computed<number | null>(() => {
	if (!user.value || !leaderboard.value.length) return null
	const entry = leaderboard.value.find((e) => e.student_id === user.value?.id)
	return entry ? entry.rank : null
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

const showLogoutConfirm = ref<boolean>(false)

function handleLogout(): void {
	showLogoutConfirm.value = true
}

function confirmLogout(): void {
	showLogoutConfirm.value = false
	authStore.logout()
	router.push('/login')
}

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
		<div class="profile-layout" :class="{ 'single-col': user?.role !== 'student' }">
			<!-- Left Column: User Card, Streak Showcase, Tier Progression -->
			<div class="profile-main-col">
				<!-- User Info Header Card -->
				<PixelCard class="user-header-card">
					<PixelCardContent>
						<div class="user-header-row">
							<div
								class="avatar-interactive-wrapper"
								title="Click to change avatar"
								@click="showAvatarPicker = true"
							>
								<PixelAvatar
									size="large"
									color="primary"
									class="profile-avatar"
									:avatar="user?.avatar"
								>
									{{ user?.name ? user.name.charAt(0).toUpperCase() : 'U' }}
								</PixelAvatar>
								<div class="avatar-edit-overlay">
									<PixelIcon name="edit" :size="12" />
								</div>
							</div>

							<div class="user-meta-info">
								<div class="name-badge-row">
									<h2 class="profile-name">{{ user?.name }}</h2>
									<PixelBadge
										:text="
											user?.role === 'admin'
												? 'ADMIN'
												: (user?.role || '').toUpperCase()
										"
										:color="
											user?.role === 'admin'
												? 'danger'
												: user?.role === 'mentor'
													? 'warning'
													: 'primary'
										"
									/>
									<!-- Top 3 Champion Badges (Student Only) -->
									<template v-if="user?.role === 'student'">
										<PixelBadge
											v-if="userRank === 1"
											text="RANK #1 CHAMPION"
											color="warning"
										/>
										<PixelBadge
											v-else-if="userRank === 2"
											text="RANK #2 RUNNER-UP"
											color="secondary"
										/>
										<PixelBadge
											v-else-if="userRank === 3"
											text="RANK #3 PODIUM"
											color="warning"
										/>
									</template>
								</div>
								<p class="profile-email">{{ user?.email }}</p>

								<div class="meta-tags-row">
									<PixelBadge
										v-if="user?.year_batch && user?.role === 'student'"
										:text="`Batch ${user.year_batch}`"
										color="secondary"
									/>
									<PixelBadge
										v-if="user?.department"
										:text="user.department"
										color="secondary"
									/>
									<PixelBadge
										v-if="user?.roll_number && user?.role === 'student'"
										:text="user.roll_number"
										color="secondary"
									/>
									<!-- XP Badge (Student Only) -->
									<PixelBadge
										v-if="user?.role === 'student'"
										:text="`${totalPoints} XP`"
										color="primary"
									/>
								</div>
							</div>

							<!-- Desktop Actions -->
							<div class="user-header-actions">
								<PixelButton
									color="secondary"
									size="small"
									icon="edit"
									@click="showAvatarPicker = true"
								>
									Avatar
								</PixelButton>

								<PixelButton
									color="danger"
									size="small"
									icon="logout"
									class="profile-logout-btn"
									@click="handleLogout"
								>
									Logout
								</PixelButton>
							</div>
						</div>
					</PixelCardContent>
				</PixelCard>

				<!-- Admin Overview Card (Admin Only) -->
				<PixelCard v-if="user?.role === 'admin'" class="role-overview-card">
					<PixelCardTitle class="section-card-title">
						<PixelSprite name="sword" :size="18" />
						<span>Administrator Privileges</span>
					</PixelCardTitle>
					<PixelCardContent>
						<p class="role-desc">
							Full administrative privileges. Manage problem pools, student cohorts,
							analytics, and platform configuration.
						</p>
						<div class="quick-nav-row">
							<PixelButton
								color="primary"
								size="small"
								icon="settings"
								@click="router.push('/admin')"
							>
								Admin Dashboard
							</PixelButton>
							<PixelButton
								color="secondary"
								size="small"
								icon="trophy"
								@click="router.push('/leaderboard')"
							>
								Leaderboard
							</PixelButton>
						</div>
					</PixelCardContent>
				</PixelCard>

				<!-- Mentor Overview Card (Mentor Only) -->
				<PixelCard v-if="user?.role === 'mentor'" class="role-overview-card">
					<PixelCardTitle class="section-card-title">
						<PixelSprite name="sword" :size="18" />
						<span>Mentor Privileges</span>
					</PixelCardTitle>
					<PixelCardContent>
						<p class="role-desc">
							Department faculty access. Author, review, and curate daily aptitude
							MCQs and coding practice problems.
						</p>
						<div class="quick-nav-row">
							<PixelButton
								color="primary"
								size="small"
								icon="edit"
								@click="router.push('/mentor')"
							>
								Question Sets
							</PixelButton>
							<PixelButton
								color="secondary"
								size="small"
								icon="trophy"
								@click="router.push('/leaderboard')"
							>
								Leaderboard
							</PixelButton>
						</div>
					</PixelCardContent>
				</PixelCard>

				<!-- Streak Showcase Box (Student Only) -->
				<PixelCard v-if="user?.role === 'student'" class="streak-box-card">
					<PixelCardTitle class="section-card-title">
						<PixelSprite name="flame" :size="18" />
						<span>Daily Consistency & Streak</span>
					</PixelCardTitle>
					<PixelCardContent>
						<div class="streak-top-row">
							<span class="streak-number">{{ streakCount }}</span>
							<div class="streak-flame-group">
								<div class="streak-flame-row">
									<span class="streak-label">Days Active Streak</span>
								</div>
								<span v-if="progress?.longest_streak" class="streak-sub">
									Personal best: {{ progress.longest_streak }} days
								</span>
							</div>
						</div>

						<div class="pixel-divider" />

						<!-- 7 Days Circles Row -->
						<div class="days-row">
							<div v-for="(day, idx) in weekDays" :key="idx" class="day-col">
								<div
									class="day-circle"
									:class="{
										'is-weekend': day.isWeekend,
										'is-solved': day.isSolved,
										'is-today': day.isCurrentDay,
									}"
								>
									<PixelIcon
										v-if="day.isSolved"
										name="check"
										:size="14"
										color="#fff"
									/>
								</div>
								<span class="day-name" :class="{ highlight: day.isCurrentDay }">
									{{ day.name }}
								</span>
							</div>
						</div>
					</PixelCardContent>
				</PixelCard>

				<!-- Tier Level Progression (Student Only) -->
				<PixelCard v-if="user?.role === 'student'" class="tier-card">
					<PixelCardTitle class="section-card-title">
						<PixelSprite name="sword" :size="18" />
						<span>Skill Tier Progression</span>
					</PixelCardTitle>
					<PixelCardContent>
						<div class="tier-labels">
							<span class="tier-name">{{ currentTier }}</span>
							<PixelBadge :text="`${totalPoints} XP`" color="primary" />
						</div>
						<PixelProgressBar
							:model-value="tierProgressPercent"
							color="warning"
							class="tier-progress-bar"
						/>
						<span class="tier-subtext"
							>Earn points daily by solving assigned questions to unlock the next
							tier</span
						>
					</PixelCardContent>
				</PixelCard>

				<!-- Duplicated Mobile Actions (Visible on Mobile Screens) -->
				<div class="mobile-logout-wrapper">
					<PixelButton
						color="secondary"
						size="medium"
						icon="edit"
						block
						@click="showAvatarPicker = true"
					>
						Change Avatar
					</PixelButton>
					<PixelButton
						color="danger"
						size="medium"
						icon="logout"
						block
						@click="handleLogout"
					>
						Logout
					</PixelButton>
				</div>
			</div>

			<!-- Right Column: Milestones & Top Peers (Batch) (Student Only) -->
			<div v-if="user?.role === 'student'" class="profile-side-col">
				<BadgesShowcase :badges="progress?.badges || []" />
				<CohortStandings :leaderboard="leaderboard" :currentUserId="user?.id" />
			</div>
		</div>

		<!-- Logout Confirmation Modal -->
		<PixelModal
			v-model="showLogoutConfirm"
			title="Confirm Log Out"
			ok-text="Log Out"
			ok-color="danger"
			cancel-text="Cancel"
			@ok="confirmLogout"
		>
			<div class="logout-confirm-content">
				<p>Are you sure you want to log out of your session?</p>
				<p class="logout-subtext">You will need to sign in again to access your account.</p>
			</div>
		</PixelModal>

		<!-- Avatar Picker Modal -->
		<AvatarPickerModal v-model="showAvatarPicker" />
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

.user-header-row {
	display: flex;
	align-items: center;
	gap: 1.5rem;
}

.avatar-interactive-wrapper {
	position: relative;
	cursor: pointer;
	flex-shrink: 0;
	border-radius: 4px;
}

.avatar-interactive-wrapper:hover .avatar-edit-overlay {
	opacity: 1;
}

.avatar-edit-overlay {
	position: absolute;
	inset: 0;
	background: rgba(0, 0, 0, 0.55);
	display: flex;
	align-items: center;
	justify-content: center;
	color: #fff;
	opacity: 0;
	transition: opacity 0.15s ease;
	border-radius: 4px;
}

.profile-avatar {
	font-size: 1.75rem;
	font-weight: 700;
	flex-shrink: 0;
	width: 68px;
	height: 68px;
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
	font-family: var(--font-pixel);
	font-size: 1.5rem;
	font-weight: normal;
	margin: 0;
	color: var(--pixel-text);
	letter-spacing: -0.01em;
}

.profile-email {
	font-size: 0.9rem;
	color: var(--pixel-text-muted);
	margin: 0;
}

.meta-tags-row {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	flex-wrap: wrap;
	margin-top: 0.35rem;
}

.section-card-title {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	font-family: var(--font-pixel);
	font-size: 13px;
	text-transform: uppercase;
}

.streak-top-row {
	display: flex;
	align-items: center;
	gap: 1.25rem;
	margin-bottom: 0.5rem;
}

.streak-number {
	font-family: var(--font-pixel);
	font-size: 3.2rem;
	font-weight: normal;
	color: #fbbf24;
	line-height: 1;
	text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.streak-flame-group {
	display: flex;
	flex-direction: column;
	gap: 2px;
}

.streak-flame-row {
	display: flex;
	align-items: center;
	gap: 0.5rem;
}

.streak-label {
	font-family: var(--font-pixel);
	font-size: 1.1rem;
	color: var(--pixel-text);
}

.streak-sub {
	font-size: 0.8rem;
	color: var(--pixel-text-dim);
}

.pixel-divider {
	height: 2px;
	background-color: var(--pixel-border);
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
	width: 36px;
	height: 36px;
	border-radius: 4px;
	border: 2px solid var(--pixel-border);
	display: flex;
	align-items: center;
	justify-content: center;
	background: var(--pixel-bg-alt);
	box-shadow: 0 2px 0 0 rgba(0, 0, 0, 0.3);
	transition: all 0.15s ease;
}

.day-circle.is-solved {
	background: var(--pixel-btn-success-bg);
	border-color: var(--pixel-btn-success-border);
	box-shadow: 0 2px 0 0 var(--pixel-btn-success-shade);
}

.day-circle.is-today:not(.is-solved) {
	border-color: var(--pixel-btn-primary-bg);
	box-shadow: 0 0 0 2px var(--pixel-btn-primary-border);
}

.day-circle.is-weekend {
	opacity: 0.45;
}

.day-name {
	font-family: var(--font-pixel);
	font-size: 0.75rem;
	color: var(--pixel-text-dim);
}

.day-name.highlight {
	color: #fbbf24;
}

.tier-labels {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 0.65rem;
}

.tier-name {
	font-family: var(--font-pixel);
	font-size: 1.05rem;
	color: var(--pixel-text);
}

.tier-progress-bar {
	margin-bottom: 0.5rem;
}

.tier-subtext {
	font-size: 0.8rem;
	color: var(--pixel-text-dim);
}

.profile-layout.single-col {
	grid-template-columns: 1fr;
	max-width: 800px;
}

.user-header-actions {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	flex-shrink: 0;
}

.role-overview-card {
	margin-top: 0.25rem;
}

.role-desc {
	font-size: 0.95rem;
	line-height: 1.5;
	color: var(--pixel-text);
	margin-bottom: 1.25rem;
}

.quick-nav-row {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	flex-wrap: wrap;
}

.mobile-logout-wrapper {
	display: none;
	margin-top: 1.25rem;
	flex-direction: column;
	gap: 0.75rem;
}

@media (max-width: 768px) {
	.user-header-row {
		flex-direction: column;
		align-items: flex-start;
		gap: 1rem;
	}

	.user-header-actions {
		display: none;
	}

	.mobile-logout-wrapper {
		display: flex;
	}
}
</style>
