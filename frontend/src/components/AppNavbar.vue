<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useColors } from 'vuestic-ui'

const router = useRouter()
const authStore = useAuthStore()
const { applyPreset } = useColors()

const isDark = ref<boolean>(false)

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
</script>

<template>
	<VaNavbar class="app-navbar" color="backgroundSecondary">
		<template #left>
			<VaNavbarItem class="brand-item" @click="router.push('/')">
				<VaIcon name="code" size="large" color="primary" />
				<span class="brand-title">zero1</span>
			</VaNavbarItem>
		</template>

		<template #center>
			<VaNavbarItem v-if="authStore.isAuthenticated" class="nav-links">
				<template v-if="authStore.userRole === 'student'">
					<VaButton
						preset="secondary"
						size="small"
						icon="event_available"
						@click="router.push('/student')"
					>
						Daily Challenge
					</VaButton>
					<VaButton
						preset="secondary"
						size="small"
						icon="emoji_events"
						@click="router.push('/leaderboard')"
					>
						Leaderboard
					</VaButton>
					<VaButton
						preset="secondary"
						size="small"
						icon="account_circle"
						@click="router.push('/profile')"
					>
						Profile
					</VaButton>
				</template>

				<template v-if="authStore.userRole === 'mentor'">
					<VaButton
						preset="secondary"
						size="small"
						icon="edit_note"
						@click="router.push('/mentor')"
					>
						My Question Set
					</VaButton>
				</template>

				<template v-if="authStore.userRole === 'admin'">
					<VaButton
						preset="secondary"
						size="small"
						icon="tune"
						@click="router.push('/admin')"
					>
						Admin Dashboard
					</VaButton>
					<VaButton
						preset="secondary"
						size="small"
						icon="emoji_events"
						@click="router.push('/leaderboard')"
					>
						Leaderboard
					</VaButton>
				</template>
			</VaNavbarItem>
		</template>

		<template #right>
			<VaNavbarItem class="user-actions">
				<!-- Student Gamification Badges -->
				<template v-if="authStore.userRole === 'student' && authStore.user">
					<VaBadge
						:text="`${authStore.user.current_streak ?? 0}d`"
						color="warning"
						title="Current Daily Streak"
					>
						<template #prepend>
							<VaIcon name="local_fire_department" size="small" />
						</template>
					</VaBadge>
					<VaBadge
						:text="`${authStore.user.total_points ?? 0} pts`"
						color="primary"
						title="Total Reward Points"
					>
						<template #prepend>
							<VaIcon name="star" size="small" />
						</template>
					</VaBadge>
				</template>

				<!-- User Tag -->
				<template v-if="authStore.isAuthenticated && authStore.user">
					<div class="user-pill-clickable" @click="router.push('/profile')">
						<span class="user-name">{{ authStore.user.name }}</span>
						<VaBadge
							:text="authStore.user.role.toUpperCase()"
							:color="authStore.user.role === 'admin' ? 'danger' : authStore.user.role === 'mentor' ? 'warning' : 'info'"
						/>
					</div>
				</template>

				<!-- Dark / Light Theme Toggle -->
				<VaButton
					preset="secondary"
					size="small"
					:icon="isDark ? 'light_mode' : 'dark_mode'"
					aria-label="Toggle theme"
					@click="toggleTheme"
				/>

				<!-- Logout / Login -->
				<VaButton
					v-if="authStore.isAuthenticated"
					preset="secondary"
					size="small"
					icon="logout"
					title="Logout"
					@click="handleLogout"
				/>
				<VaButton
					v-else
					size="small"
					color="primary"
					icon="login"
					@click="router.push('/login')"
				>
					Login
				</VaButton>
			</VaNavbarItem>
		</template>
	</VaNavbar>
</template>

<style scoped>
.app-navbar {
	border-bottom: 1px solid var(--va-background-border);
	position: sticky;
	top: 0;
	z-index: 1000;
	padding: 0.5rem 1.5rem;
}

.brand-item {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	cursor: pointer;
}

.brand-title {
	font-weight: 700;
	font-size: 1.25rem;
	letter-spacing: -0.025em;
	color: var(--va-text-primary);
}

.nav-links {
	display: flex;
	align-items: center;
	gap: 0.5rem;
}

.user-actions {
	display: flex;
	align-items: center;
	gap: 0.75rem;
}

.user-name {
	font-size: 0.875rem;
	font-weight: 500;
	color: var(--va-text-primary);
}
</style>
