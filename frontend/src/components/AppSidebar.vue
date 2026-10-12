<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import UserProfileModal from '@/components/UserProfileModal.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'
import PixelAvatar from '@/components/pixel/PixelAvatar.vue'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelButton from '@/components/pixel/PixelButton.vue'
import ThemeToggle from '@/components/common/ThemeToggle.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isDesktopCollapsed = ref<boolean>(false)
const isTablet = ref<boolean>(false)
const showProfileModal = ref<boolean>(false)

const isWorkspaceRoute = computed<boolean>(() => route.path.startsWith('/workspace'))

function checkScreenSize(): void {
	if (typeof window !== 'undefined') {
		const width = window.innerWidth
		isTablet.value = width > 768 && width < 1024
		// On tablet, collapse sidebar by default if no explicit user preference
		if (isTablet.value && localStorage.getItem('sidebar_collapsed') === null) {
			isDesktopCollapsed.value = true
		}
	}
}

function toggleCollapse(): void {
	isDesktopCollapsed.value = !isDesktopCollapsed.value
	localStorage.setItem('sidebar_collapsed', isDesktopCollapsed.value ? 'true' : 'false')
}

onMounted(() => {
	const savedCollapsed = localStorage.getItem('sidebar_collapsed')
	if (savedCollapsed === 'true') {
		isDesktopCollapsed.value = true
	}

	checkScreenSize()
	if (typeof window !== 'undefined') {
		window.addEventListener('resize', checkScreenSize)
	}
})

onUnmounted(() => {
	if (typeof window !== 'undefined') {
		window.removeEventListener('resize', checkScreenSize)
	}
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

function navigateTo(path: string): void {
	router.push(path)
	// On tablet, close the overlay after navigation
	if (isTablet.value) {
		isDesktopCollapsed.value = true
	}
}
</script>

<template>
	<aside
		:class="[
			'app-sidebar',
			{
				'is-collapsed': isDesktopCollapsed,
				'sidebar--hidden-mobile': isWorkspaceRoute,
				'tablet-overlay': isTablet && !isDesktopCollapsed,
			},
		]"
	>
		<!-- Tablet Backdrop when overlay is active -->
		<Teleport to="body">
			<div
				v-if="isTablet && !isDesktopCollapsed"
				class="sidebar-backdrop"
				@click="isDesktopCollapsed = true"
			/>
		</Teleport>
		<!-- Brand Logo & Collapse Toggle (Desktop Header) -->
		<div class="sidebar-header">
			<div class="sidebar-brand" @click="navigateTo('/')" title="ZERO1 Home">
				<div class="brand-icon-box">
					<PixelSprite name="sword" :size="24" />
				</div>
				<span v-if="!isDesktopCollapsed" class="brand-title">ZERO1</span>
			</div>

			<button
				type="button"
				class="sidebar-collapse-btn"
				:title="isDesktopCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
				@click="toggleCollapse"
			>
				<PixelIcon
					:name="isDesktopCollapsed ? 'chevron-right' : 'chevron-left'"
					:size="14"
				/>
			</button>
		</div>

		<div class="pixel-divider" />

		<!-- Role-based Navigation Links -->
		<nav class="sidebar-nav">
			<!-- Admin Navigation -->
			<template v-if="authStore.userRole === 'admin'">
				<button
					type="button"
					:class="['nav-item', { 'nav-item--active': route.path === '/admin' }]"
					title="Admin Dashboard"
					@click="navigateTo('/admin')"
				>
					<PixelIcon name="settings" :size="18" />
					<span v-if="!isDesktopCollapsed" class="nav-label">Admin Dashboard</span>
					<span class="mobile-nav-label">Admin</span>
				</button>

				<button
					type="button"
					:class="['nav-item', { 'nav-item--active': route.path === '/leaderboard' }]"
					title="Leaderboard"
					@click="navigateTo('/leaderboard')"
				>
					<PixelIcon name="trophy" :size="18" />
					<span v-if="!isDesktopCollapsed" class="nav-label">Leaderboard</span>
					<span class="mobile-nav-label">Ranks</span>
				</button>

				<button
					type="button"
					:class="['nav-item', { 'nav-item--active': route.path === '/profile' }]"
					title="Profile"
					@click="navigateTo('/profile')"
				>
					<PixelIcon name="user" :size="18" />
					<span v-if="!isDesktopCollapsed" class="nav-label">Profile</span>
					<span class="mobile-nav-label">Profile</span>
				</button>
			</template>

			<!-- Mentor Navigation -->
			<template v-if="authStore.userRole === 'mentor'">
				<button
					type="button"
					:class="['nav-item', { 'nav-item--active': route.path === '/mentor' }]"
					title="Question Set"
					@click="navigateTo('/mentor')"
				>
					<PixelIcon name="edit" :size="18" />
					<span v-if="!isDesktopCollapsed" class="nav-label">Question Set</span>
					<span class="mobile-nav-label">Questions</span>
				</button>

				<button
					type="button"
					:class="['nav-item', { 'nav-item--active': route.path === '/leaderboard' }]"
					title="Leaderboard"
					@click="navigateTo('/leaderboard')"
				>
					<PixelIcon name="trophy" :size="18" />
					<span v-if="!isDesktopCollapsed" class="nav-label">Leaderboard</span>
					<span class="mobile-nav-label">Ranks</span>
				</button>

				<button
					type="button"
					:class="['nav-item', { 'nav-item--active': route.path === '/profile' }]"
					title="Profile"
					@click="navigateTo('/profile')"
				>
					<PixelIcon name="user" :size="18" />
					<span v-if="!isDesktopCollapsed" class="nav-label">Profile</span>
					<span class="mobile-nav-label">Profile</span>
				</button>
			</template>

			<!-- Student Navigation -->
			<template v-if="authStore.userRole === 'student'">
				<button
					type="button"
					:class="['nav-item', { 'nav-item--active': route.path === '/student' }]"
					title="Daily Quests"
					@click="navigateTo('/student')"
				>
					<PixelIcon name="calendar" :size="18" />
					<span v-if="!isDesktopCollapsed" class="nav-label">Daily Quests</span>
					<span class="mobile-nav-label">Quests</span>
				</button>

				<button
					type="button"
					:class="['nav-item', { 'nav-item--active': route.path === '/leaderboard' }]"
					title="Leaderboard"
					@click="navigateTo('/leaderboard')"
				>
					<PixelIcon name="trophy" :size="18" />
					<span v-if="!isDesktopCollapsed" class="nav-label">Leaderboard</span>
					<span class="mobile-nav-label">Ranks</span>
				</button>

				<button
					type="button"
					:class="['nav-item', { 'nav-item--active': route.path === '/profile' }]"
					title="My Profile"
					@click="navigateTo('/profile')"
				>
					<PixelIcon name="user" :size="18" />
					<span v-if="!isDesktopCollapsed" class="nav-label">My Profile</span>
					<span class="mobile-nav-label">Profile</span>
				</button>
			</template>
		</nav>

		<!-- Spacer to push bottom section down -->
		<div class="sidebar-spacer" />

		<div class="pixel-divider" />

		<!-- Sidebar Bottom / User Profile & Controls (Desktop Only) -->
		<div v-if="authStore.isAuthenticated && authStore.user" class="sidebar-user-block">
			<div
				class="user-row clickable-user"
				:title="authStore.user.name"
				@click="navigateTo('/profile')"
			>
				<PixelAvatar size="small" color="primary" :avatar="authStore.user.avatar">
					{{ authStore.user.name.charAt(0).toUpperCase() }}
				</PixelAvatar>
				<div v-if="!isDesktopCollapsed" class="user-info">
					<span class="user-display-name">{{ authStore.user.name }}</span>
					<div class="role-badge-row">
						<PixelBadge
							:text="
								authStore.user.role === 'admin'
									? 'ADMIN'
									: authStore.user.role.toUpperCase()
							"
							:color="
								authStore.user.role === 'admin'
									? 'danger'
									: authStore.user.role === 'mentor'
										? 'warning'
										: 'primary'
							"
						/>
					</div>
				</div>
			</div>

			<!-- Student XP & Streak Stats -->
			<div
				v-if="authStore.userRole === 'student' && !isDesktopCollapsed"
				class="student-stats-row"
			>
				<div class="streak-badge" title="Current Daily Streak">
					<PixelSprite name="flame" :size="16" />
					<span class="streak-text">{{ authStore.user.current_streak ?? 0 }}d</span>
				</div>
				<PixelBadge :text="`${authStore.user.total_points ?? 0} XP`" color="primary" />
			</div>

			<!-- Controls: Theme Toggle & Logout -->
			<div class="sidebar-actions">
				<ThemeToggle
					size="small"
					:show-label="!isDesktopCollapsed"
					class="sidebar-theme-toggle"
				/>
				<PixelButton
					color="danger"
					size="small"
					block
					icon="logout"
					title="Logout"
					@click="handleLogout"
				>
					<span v-if="!isDesktopCollapsed">Logout</span>
				</PixelButton>
			</div>
		</div>

		<!-- User Profile Popup Modal -->
		<UserProfileModal v-model="showProfileModal" :user="authStore.user" />

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
	</aside>
</template>

<style scoped>
.app-sidebar {
	display: flex;
	flex-direction: column;
	width: 250px;
	height: 100vh;
	position: sticky;
	top: 0;
	background-color: var(--pixel-surface);
	border-right: 3px solid var(--pixel-border);
	box-shadow: 4px 0 0 0 var(--pixel-border-dark);
	padding: 1.25rem 0.85rem;
	user-select: none;
	flex-shrink: 0;
	z-index: 100;
	transition:
		width 0.15s ease,
		padding 0.15s ease;
}

.app-sidebar.is-collapsed {
	width: 72px;
	padding: 1.25rem 0.5rem;
}

.sidebar-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.5rem;
	padding: 0.2rem 0.25rem;
}

.app-sidebar.is-collapsed .sidebar-header {
	flex-direction: column;
	justify-content: center;
	gap: 0.75rem;
	padding: 0;
}

.sidebar-brand {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	cursor: pointer;
	overflow: hidden;
}

.brand-icon-box {
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}

.brand-title {
	font-family: var(--font-pixel);
	font-size: 1.35rem;
	font-weight: normal;
	letter-spacing: 0.04em;
	color: var(--pixel-text);
	text-shadow: 0 2px 0 var(--pixel-border-dark);
	white-space: nowrap;
}

.sidebar-collapse-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	width: 26px;
	height: 26px;
	background: var(--pixel-surface-alt);
	border: 2px solid var(--pixel-border);
	border-radius: 2px;
	color: var(--pixel-text-dim);
	cursor: pointer;
	padding: 0;
	flex-shrink: 0;
	transition:
		background 0.1s,
		color 0.1s;
}

.sidebar-collapse-btn:hover {
	background: var(--pixel-surface-raised);
	color: var(--pixel-text);
	border-color: var(--pixel-border-bright);
}

.pixel-divider {
	height: 2px;
	background-color: var(--pixel-border);
	margin: 0.85rem 0;
}

.sidebar-nav {
	display: flex;
	flex-direction: column;
	gap: 0.4rem;
}

.nav-item {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	width: 100%;
	padding: 8px 12px;
	background-color: transparent;
	color: var(--pixel-text-muted);
	border: 2px solid transparent;
	border-radius: 3px;
	font-family: var(--font-pixel);
	font-size: 12px;
	text-transform: uppercase;
	letter-spacing: 0.04em;
	cursor: pointer;
	transition: all 0.08s ease;
	text-align: left;
}

.app-sidebar.is-collapsed .nav-item {
	justify-content: center;
	padding: 10px 0;
	gap: 0;
}

.nav-item:hover {
	background-color: var(--pixel-surface-alt);
	color: var(--pixel-text);
	border-color: var(--pixel-border);
}

.nav-item--active {
	background-color: var(--pixel-btn-primary-bg);
	border-color: var(--pixel-btn-primary-border);
	box-shadow: 0 3px 0 0 var(--pixel-btn-primary-shade);
	color: var(--pixel-btn-primary-text);
	transform: translateY(-1px);
}

.nav-label {
	flex: 1;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.mobile-nav-label {
	display: none;
}

.sidebar-spacer {
	flex: 1;
}

.sidebar-user-block {
	display: flex;
	flex-direction: column;
	gap: 0.75rem;
	padding: 0.4rem 0.2rem;
}

.app-sidebar.is-collapsed .sidebar-user-block {
	padding: 0.4rem 0;
	align-items: center;
}

.user-row {
	display: flex;
	align-items: center;
	gap: 0.65rem;
}

.app-sidebar.is-collapsed .user-row {
	justify-content: center;
	padding: 0;
}

.clickable-user {
	cursor: pointer;
	padding: 0.4rem;
	border: 1px solid transparent;
	border-radius: 4px;
	transition: all 0.1s;
}

.clickable-user:hover {
	background-color: var(--pixel-surface-alt);
	border-color: var(--pixel-border);
}

.user-info {
	display: flex;
	flex-direction: column;
	gap: 0.2rem;
	overflow: hidden;
}

.user-display-name {
	font-family: var(--font-body);
	font-size: 0.875rem;
	font-weight: 600;
	color: var(--pixel-text);
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.role-badge-row {
	display: flex;
}

.student-stats-row {
	display: flex;
	align-items: center;
	gap: 0.6rem;
}

.streak-badge {
	display: inline-flex;
	align-items: center;
	gap: 4px;
	background-color: var(--pixel-surface-raised);
	border: 1px solid var(--pixel-border);
	padding: 2px 6px;
	border-radius: 3px;
}

.streak-text {
	font-family: var(--font-pixel);
	font-size: 11px;
	color: var(--pixel-warning);
}

.sidebar-actions {
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
	margin-top: 0.25rem;
}

.sidebar-theme-toggle {
	width: 100%;
	height: 32px;
}

.app-sidebar.is-collapsed .sidebar-theme-toggle {
	width: 32px;
}

.app-sidebar.is-collapsed .sidebar-actions {
	align-items: center;
	width: 100%;
}

/* =========================================================
   SPOTIFY-STYLE MOBILE BOTTOM NAVIGATION BAR
   ========================================================= */
@media (max-width: 768px) {
	.app-sidebar {
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		top: auto;
		width: 100% !important;
		height: 56px;
		flex-direction: row;
		align-items: center;
		justify-content: space-around;
		padding: 0 0.5rem;
		border-right: none;
		border-top: 3px solid var(--pixel-border);
		box-shadow: 0 -3px 0 0 var(--pixel-border-dark);
		background-color: var(--pixel-surface);
		z-index: 1000;
	}

	.sidebar-header,
	.pixel-divider,
	.sidebar-spacer,
	.sidebar-user-block,
	.sidebar-collapse-btn {
		display: none !important;
	}

	.sidebar-nav {
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: space-around;
		width: 100%;
		height: 100%;
		gap: 0;
	}

	.nav-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 3px;
		height: 100%;
		flex: 1;
		padding: 4px 6px;
		border: none;
		background: transparent;
		border-radius: 0;
		color: var(--pixel-text-muted);
		transform: none !important;
	}

	.nav-item:hover {
		background: transparent;
		color: var(--pixel-text);
		border: none;
	}

	.nav-item--active {
		background: transparent;
		box-shadow: none;
		color: var(--pixel-primary);
		border: none;
		border-top: 2px solid var(--pixel-primary);
		padding: 28px 0 !important;
	}

	.nav-label {
		display: none !important;
	}

	.mobile-nav-label {
		display: block !important;
		font-family: var(--font-pixel);
		font-size: 9px;
		line-height: 1;
		text-transform: uppercase;
		letter-spacing: 0.02em;
		white-space: nowrap;
	}

	.sidebar--hidden-mobile {
		display: none !important;
	}
}

/* =========================================================
   TABLET LAYOUT FLOATING OVERLAY (769px - 1024px)
   ========================================================= */
.sidebar-backdrop {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background-color: rgba(0, 0, 0, 0.65);
	backdrop-filter: blur(2px);
	z-index: 998;
}

.tablet-sidebar-spacer {
	width: 72px;
	height: 100vh;
	flex-shrink: 0;
}

@media (min-width: 769px) and (max-width: 1024px) {
	.app-sidebar.tablet-overlay {
		position: fixed !important;
		top: 0;
		left: 0;
		width: 250px !important;
		height: 100vh;
		z-index: 999;
		box-shadow: 6px 0 24px rgba(0, 0, 0, 0.7);
	}
}
</style>
