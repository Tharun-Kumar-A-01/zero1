<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useColors } from 'vuestic-ui'
import UserProfileModal from '@/components/UserProfileModal.vue'
import XpStarBadge from '@/components/common/XpStarBadge.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { applyPreset } = useColors()

const isDark = ref<boolean>(false)
const showProfileModal = ref<boolean>(false)

function toggleTheme(): void {
	isDark.value = !isDark.value
	const preset = isDark.value ? 'dark' : 'light'
	applyPreset(preset)
	if (isDark.value) {
		document.documentElement.classList.add('dark')
		localStorage.setItem('theme', 'dark')
	} else {
		document.documentElement.classList.remove('dark')
		localStorage.setItem('theme', 'light')
	}
}

onMounted(() => {
	const saved = localStorage.getItem('theme')
	if (saved === 'dark' || (!saved && typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
		isDark.value = true
		applyPreset('dark')
		document.documentElement.classList.add('dark')
	} else {
		isDark.value = false
		applyPreset('light')
		document.documentElement.classList.remove('dark')
	}
})

function handleLogout(): void {
	authStore.logout()
	router.push('/login')
}

function navigateTo(path: string): void {
	router.push(path)
}
</script>

<template>
	<VaSidebar class="app-sidebar" color="backgroundSecondary" width="260px">
		<!-- Brand Logo -->
		<div class="sidebar-brand" @click="navigateTo('/')">
			<VaIcon name="code" size="32px" color="primary" />
			<span class="brand-title">zero1</span>
		</div>

		<VaDivider class="brand-divider" />

		<!-- Role-based Navigation Links -->
		<div class="sidebar-nav">
			<!-- Admin Navigation -->
			<template v-if="authStore.userRole === 'admin'">
				<VaSidebarItem
					:active="route.path === '/admin'"
					@click="navigateTo('/admin')"
				>
					<VaSidebarItemContent>
						<VaIcon name="tune" />
						<VaSidebarItemTitle>Admin Dashboard</VaSidebarItemTitle>
					</VaSidebarItemContent>
				</VaSidebarItem>

				<VaSidebarItem
					:active="route.path === '/leaderboard'"
					@click="navigateTo('/leaderboard')"
				>
					<VaSidebarItemContent>
						<VaIcon name="emoji_events" />
						<VaSidebarItemTitle>Leaderboard</VaSidebarItemTitle>
					</VaSidebarItemContent>
				</VaSidebarItem>
			</template>

			<!-- Mentor Navigation -->
			<template v-if="authStore.userRole === 'mentor'">
				<VaSidebarItem
					:active="route.path === '/mentor'"
					@click="navigateTo('/mentor')"
				>
					<VaSidebarItemContent>
						<VaIcon name="edit_note" />
						<VaSidebarItemTitle>Question Set</VaSidebarItemTitle>
					</VaSidebarItemContent>
				</VaSidebarItem>

				<VaSidebarItem
					:active="route.path === '/leaderboard'"
					@click="navigateTo('/leaderboard')"
				>
					<VaSidebarItemContent>
						<VaIcon name="emoji_events" />
						<VaSidebarItemTitle>Leaderboard</VaSidebarItemTitle>
					</VaSidebarItemContent>
				</VaSidebarItem>
			</template>

			<!-- Student Navigation -->
			<template v-if="authStore.userRole === 'student'">
				<VaSidebarItem
					:active="route.path === '/student'"
					@click="navigateTo('/student')"
				>
					<VaSidebarItemContent>
						<VaIcon name="event_available" />
						<VaSidebarItemTitle>Daily Practice</VaSidebarItemTitle>
					</VaSidebarItemContent>
				</VaSidebarItem>

				<VaSidebarItem
					:active="route.path === '/leaderboard'"
					@click="navigateTo('/leaderboard')"
				>
					<VaSidebarItemContent>
						<VaIcon name="emoji_events" />
						<VaSidebarItemTitle>Leaderboard</VaSidebarItemTitle>
					</VaSidebarItemContent>
				</VaSidebarItem>

				<VaSidebarItem
					:active="route.path === '/profile'"
					@click="navigateTo('/profile')"
				>
					<VaSidebarItemContent>
						<VaIcon name="account_circle" />
						<VaSidebarItemTitle>My Profile</VaSidebarItemTitle>
					</VaSidebarItemContent>
				</VaSidebarItem>
			</template>
		</div>

		<!-- Spacer to push bottom section down -->
		<div class="sidebar-spacer"></div>

		<VaDivider class="footer-divider" />

		<!-- Sidebar Bottom / User Profile & Controls -->
		<div v-if="authStore.isAuthenticated && authStore.user" class="sidebar-user-block">
			<div class="user-row clickable-user" @click="navigateTo('/profile')">
				<VaAvatar size="small" color="primary">
					{{ authStore.user.name.charAt(0).toUpperCase() }}
				</VaAvatar>
				<div class="user-info">
					<span class="user-display-name">{{ authStore.user.name }}</span>
					<div class="role-badge-row">
						<VaBadge
							:text="authStore.user.role === 'admin' ? 'SYSTEM ADMINISTRATOR' : authStore.user.role.toUpperCase()"
							:color="authStore.user.role === 'admin' ? 'danger' : authStore.user.role === 'mentor' ? 'warning' : 'info'"
						/>
					</div>
				</div>
			</div>

			<!-- Student XP & Streak Stats -->
			<div v-if="authStore.userRole === 'student'" class="student-stats-row">
				<VaBadge
					:text="`${authStore.user.current_streak ?? 0}d`"
					color="warning"
					title="Current Daily Streak"
				>
					<template #prepend>
						<VaIcon name="local_fire_department" size="small" />
					</template>
				</VaBadge>
				<XpStarBadge
					:points="authStore.user.total_points ?? 0"
					size="small"
				/>
			</div>

			<!-- Controls: Theme Switch and Logout -->
			<div class="sidebar-actions">
				<VaButton
					preset="secondary"
					size="small"
					class="action-btn"
					:icon="isDark ? 'light_mode' : 'dark_mode'"
					@click="toggleTheme"
				>
					{{ isDark ? 'Light Mode' : 'Dark Mode' }}
				</VaButton>

				<VaButton
					preset="secondary"
					size="small"
					class="action-btn logout-btn"
					icon="logout"
					@click="handleLogout"
				>
					Logout
				</VaButton>
			</div>
		</div>

		<!-- User Profile Popup Modal -->
		<UserProfileModal
			v-model="showProfileModal"
			:user="authStore.user"
		/>
	</VaSidebar>
</template>

<style scoped>
.app-sidebar {
	display: flex;
	flex-direction: column;
	height: 100vh;
	position: sticky;
	top: 0;
	border-right: 1px solid var(--va-background-border);
	padding: 1rem 0.75rem;
	user-select: none;
	flex-shrink: 0;
}

.sidebar-brand {
	display: flex;
	align-items: center;
	gap: 0.625rem;
	padding: 0.5rem 0.75rem;
	cursor: pointer;
}

.brand-title {
	font-size: 1.25rem;
	font-weight: 800;
	letter-spacing: -0.5px;
	color: var(--va-text-primary);
}

.brand-divider {
	margin: 0.75rem 0;
}

.sidebar-nav {
	display: flex;
	flex-direction: column;
	gap: 0.25rem;
}

.sidebar-spacer {
	flex: 1;
}

.footer-divider {
	margin: 0.75rem 0;
}

.sidebar-user-block {
	display: flex;
	flex-direction: column;
	gap: 0.75rem;
	padding: 0.25rem 0.5rem;
}

.user-row {
	display: flex;
	align-items: center;
	gap: 0.625rem;
}

.clickable-user {
	cursor: pointer;
	padding: 0.375rem;
	border-radius: 4px;
	transition: background-color 0.2s;
}

.clickable-user:hover {
	background-color: var(--va-background-element);
}

.user-info {
	display: flex;
	flex-direction: column;
	gap: 0.25rem;
	overflow: hidden;
}

.user-display-name {
	font-size: 0.875rem;
	font-weight: 600;
	color: var(--va-text-primary);
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.role-badge-row {
	display: flex;
}

.student-stats-row {
	display: flex;
	gap: 0.5rem;
}

.sidebar-actions {
	display: flex;
	flex-direction: column;
	gap: 0.375rem;
	margin-top: 0.25rem;
}

.action-btn {
	justify-content: flex-start;
	width: 100%;
}

.logout-btn {
	color: var(--va-danger);
}
</style>
