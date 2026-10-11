<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import PixelButton from '@/components/pixel/PixelButton.vue'
import PixelAvatar from '@/components/pixel/PixelAvatar.vue'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'

const router = useRouter()
const authStore = useAuthStore()

onMounted(() => {
  if (typeof document !== 'undefined') {
    document.documentElement.classList.add('dark')
  }
})

function handleLogout(): void {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <header class="app-navbar">
    <div class="navbar-left">
      <div class="brand-item" @click="router.push('/')">
        <PixelSprite name="sword" :size="24" />
        <span class="brand-title">ZERO1</span>
      </div>
    </div>

    <div class="navbar-center">
      <div v-if="authStore.isAuthenticated" class="nav-links">
        <template v-if="authStore.userRole === 'student'">
          <PixelButton
            color="secondary"
            size="small"
            icon="calendar"
            @click="router.push('/student')"
          >
            Daily Challenge
          </PixelButton>
          <PixelButton
            color="secondary"
            size="small"
            icon="trophy"
            @click="router.push('/leaderboard')"
          >
            Leaderboard
          </PixelButton>
          <PixelButton
            color="secondary"
            size="small"
            icon="user"
            @click="router.push('/profile')"
          >
            Profile
          </PixelButton>
        </template>

        <template v-if="authStore.userRole === 'mentor'">
          <PixelButton
            color="secondary"
            size="small"
            icon="edit"
            @click="router.push('/mentor')"
          >
            Question Set
          </PixelButton>
        </template>

        <template v-if="authStore.userRole === 'admin'">
          <PixelButton
            color="secondary"
            size="small"
            icon="settings"
            @click="router.push('/admin')"
          >
            Admin Hub
          </PixelButton>
        </template>
      </div>
    </div>

    <div class="navbar-right">
      <div v-if="authStore.isAuthenticated && authStore.user" class="user-profile-menu">
        <PixelAvatar size="small" color="primary" :avatar="authStore.user.avatar">
          {{ authStore.user.name.charAt(0).toUpperCase() }}
        </PixelAvatar>
        <span class="user-name">{{ authStore.user.name }}</span>
        <PixelBadge
          :text="authStore.user.role.toUpperCase()"
          :color="authStore.user.role === 'admin' ? 'danger' : authStore.user.role === 'mentor' ? 'warning' : 'primary'"
        />
        <PixelButton
          color="danger"
          size="small"
          icon="logout"
          @click="handleLogout"
        >
          Logout
        </PixelButton>
      </div>
      <div v-else class="auth-buttons">
        <PixelButton
          color="primary"
          size="small"
          icon="user"
          @click="router.push('/login')"
        >
          Login
        </PixelButton>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 1.25rem;
  background-color: var(--pixel-surface);
  border-bottom: 2px solid var(--pixel-border);
  box-shadow: 0 3px 0 0 var(--pixel-border-dark);
  z-index: 50;
}

.navbar-left {
  display: flex;
  align-items: center;
}

.brand-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.brand-title {
  font-family: var(--font-pixel);
  font-size: 1.25rem;
  color: var(--pixel-text);
  margin: 0;
}

.navbar-center {
  display: flex;
  align-items: center;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 8px;
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-profile-menu {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  color: var(--pixel-text);
}

.auth-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
