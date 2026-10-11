<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import UserProfileModal from '@/components/UserProfileModal.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'
import PixelAvatar from '@/components/pixel/PixelAvatar.vue'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelButton from '@/components/pixel/PixelButton.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isDark = ref<boolean>(true)
const showProfileModal = ref<boolean>(false)

function toggleTheme(): void {
  isDark.value = !isDark.value
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
    document.documentElement.classList.add('dark')
  } else {
    isDark.value = false
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
  <aside class="app-sidebar">
    <!-- Brand Logo -->
    <div class="sidebar-brand" @click="navigateTo('/')">
      <div class="brand-icon-box">
        <PixelSprite name="sword" :size="24" />
      </div>
      <span class="brand-title">ZERO1</span>
    </div>

    <div class="pixel-divider" />

    <!-- Role-based Navigation Links -->
    <nav class="sidebar-nav">
      <!-- Admin Navigation -->
      <template v-if="authStore.userRole === 'admin'">
        <button
          type="button"
          :class="['nav-item', { 'nav-item--active': route.path === '/admin' }]"
          @click="navigateTo('/admin')"
        >
          <PixelIcon name="settings" :size="16" />
          <span class="nav-label">Admin Dashboard</span>
        </button>

        <button
          type="button"
          :class="['nav-item', { 'nav-item--active': route.path === '/leaderboard' }]"
          @click="navigateTo('/leaderboard')"
        >
          <PixelIcon name="trophy" :size="16" />
          <span class="nav-label">Leaderboard</span>
        </button>
      </template>

      <!-- Mentor Navigation -->
      <template v-if="authStore.userRole === 'mentor'">
        <button
          type="button"
          :class="['nav-item', { 'nav-item--active': route.path === '/mentor' }]"
          @click="navigateTo('/mentor')"
        >
          <PixelIcon name="edit" :size="16" />
          <span class="nav-label">Question Set</span>
        </button>

        <button
          type="button"
          :class="['nav-item', { 'nav-item--active': route.path === '/leaderboard' }]"
          @click="navigateTo('/leaderboard')"
        >
          <PixelIcon name="trophy" :size="16" />
          <span class="nav-label">Leaderboard</span>
        </button>
      </template>

      <!-- Student Navigation -->
      <template v-if="authStore.userRole === 'student'">
        <button
          type="button"
          :class="['nav-item', { 'nav-item--active': route.path === '/student' }]"
          @click="navigateTo('/student')"
        >
          <PixelIcon name="calendar" :size="16" />
          <span class="nav-label">Daily Practice</span>
        </button>

        <button
          type="button"
          :class="['nav-item', { 'nav-item--active': route.path === '/leaderboard' }]"
          @click="navigateTo('/leaderboard')"
        >
          <PixelIcon name="trophy" :size="16" />
          <span class="nav-label">Leaderboard</span>
        </button>

        <button
          type="button"
          :class="['nav-item', { 'nav-item--active': route.path === '/profile' }]"
          @click="navigateTo('/profile')"
        >
          <PixelIcon name="user" :size="16" />
          <span class="nav-label">My Profile</span>
        </button>
      </template>
    </nav>

    <!-- Spacer to push bottom section down -->
    <div class="sidebar-spacer" />

    <div class="pixel-divider" />

    <!-- Sidebar Bottom / User Profile & Controls -->
    <div v-if="authStore.isAuthenticated && authStore.user" class="sidebar-user-block">
      <div class="user-row clickable-user" @click="navigateTo('/profile')">
        <PixelAvatar size="small" color="primary">
          {{ authStore.user.name.charAt(0).toUpperCase() }}
        </PixelAvatar>
        <div class="user-info">
          <span class="user-display-name">{{ authStore.user.name }}</span>
          <div class="role-badge-row">
            <PixelBadge
              :text="authStore.user.role === 'admin' ? 'ADMIN' : authStore.user.role.toUpperCase()"
              :color="authStore.user.role === 'admin' ? 'danger' : authStore.user.role === 'mentor' ? 'warning' : 'primary'"
            />
          </div>
        </div>
      </div>

      <!-- Student XP & Streak Stats -->
      <div v-if="authStore.userRole === 'student'" class="student-stats-row">
        <div class="streak-badge" title="Current Daily Streak">
          <PixelSprite name="flame" :size="16" />
          <span class="streak-text">{{ authStore.user.current_streak ?? 0 }}d</span>
        </div>
        <PixelBadge :text="`${authStore.user.total_points ?? 0} XP`" color="primary" />
      </div>

      <!-- Controls: Theme Switch and Logout -->
      <div class="sidebar-actions">
        <PixelButton
          color="secondary"
          size="small"
          block
          @click="toggleTheme"
        >
          <PixelIcon :name="isDark ? 'star' : 'heart'" :size="14" />
          {{ isDark ? 'Tavern Dark' : 'Daylight' }}
        </PixelButton>

        <PixelButton
          color="danger"
          size="small"
          block
          icon="logout"
          @click="handleLogout"
        >
          Logout
        </PixelButton>
      </div>
    </div>

    <!-- User Profile Popup Modal -->
    <UserProfileModal
      v-model="showProfileModal"
      :user="authStore.user"
    />
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
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.4rem 0.6rem;
  cursor: pointer;
}

.brand-icon-box {
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-title {
  font-family: var(--font-pixel);
  font-size: 1.35rem;
  font-weight: normal;
  letter-spacing: 0.04em;
  color: var(--pixel-text);
  text-shadow: 0 2px 0 var(--pixel-border-dark);
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

.nav-item:hover {
  background-color: var(--pixel-surface-alt);
  color: var(--pixel-text);
  border-color: var(--pixel-border);
}

.nav-item--active {
  background-color: var(--pixel-btn-primary-bg);
  border-color: var(--pixel-btn-primary-border);
  box-shadow: 0 3px 0 0 var(--pixel-btn-primary-shade);
  color: #fff;
  transform: translateY(-1px);
}

.nav-label {
  flex: 1;
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

.user-row {
  display: flex;
  align-items: center;
  gap: 0.65rem;
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
  background-color: #2b1704;
  border: 1px solid #7e4507;
  padding: 2px 6px;
  border-radius: 3px;
}

.streak-text {
  font-family: var(--font-pixel);
  font-size: 11px;
  color: #fbbf24;
}

.sidebar-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.25rem;
}
</style>
