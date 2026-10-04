import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginView from '@/views/LoginView.vue'
import StudentView from '@/views/StudentView.vue'
import MentorView from '@/views/MentorView.vue'
import AdminView from '@/views/AdminView.vue'
import LeaderboardView from '@/views/LeaderboardView.vue'
import ProfileView from '@/views/ProfileView.vue'
import CodingWorkspaceView from '@/views/CodingWorkspaceView.vue'

const routes: RouteRecordRaw[] = [
	{
		path: '/login',
		name: 'login',
		component: LoginView,
		meta: { guestOnly: true },
	},
	{
		path: '/',
		name: 'home',
		redirect: () => {
			const authStore = useAuthStore()
			if (!authStore.isAuthenticated) {
				return '/login'
			}
			if (authStore.userRole === 'admin') {
				return '/admin'
			}
			if (authStore.userRole === 'mentor') {
				return '/mentor'
			}
			return '/student'
		},
	},
	{
		path: '/student',
		name: 'student',
		component: StudentView,
		meta: { requiresAuth: true, roles: ['student', 'admin'] },
	},
	{
		path: '/mentor',
		name: 'mentor',
		component: MentorView,
		meta: { requiresAuth: true, roles: ['mentor', 'admin'] },
	},
	{
		path: '/admin',
		name: 'admin',
		component: AdminView,
		meta: { requiresAuth: true, roles: ['admin'] },
	},
	{
		path: '/leaderboard',
		name: 'leaderboard',
		component: LeaderboardView,
		meta: { requiresAuth: true },
	},
	{
		path: '/profile',
		name: 'profile',
		component: ProfileView,
		meta: { requiresAuth: true },
	},
	{
		path: '/workspace/coding/:assignmentId',
		name: 'coding-workspace',
		component: CodingWorkspaceView,
		meta: { requiresAuth: true, roles: ['student', 'admin'] },
	},
	{
		path: '/:pathMatch(.*)*',
		redirect: '/',
	},
]

const router = createRouter({
	history: createWebHistory(import.meta.env.BASE_URL),
	routes,
})

router.beforeEach(async (to) => {
	const authStore = useAuthStore()

	// If token exists but user profile not loaded, fetch it
	if (authStore.isAuthenticated && !authStore.user) {
		await authStore.fetchProfile()
	}

	if (to.meta.requiresAuth && !authStore.isAuthenticated) {
		return '/login'
	}

	if (to.meta.guestOnly && authStore.isAuthenticated) {
		if (authStore.userRole === 'admin') return '/admin'
		if (authStore.userRole === 'mentor') return '/mentor'
		return '/student'
	}

	if (to.meta.roles && Array.isArray(to.meta.roles)) {
		const allowedRoles = to.meta.roles as string[]
		if (authStore.userRole && !allowedRoles.includes(authStore.userRole)) {
			if (authStore.userRole === 'admin') return '/admin'
			if (authStore.userRole === 'mentor') return '/mentor'
			return '/student'
		}
	}
})

export default router
