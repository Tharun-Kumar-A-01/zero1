<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import PixelCard from '@/components/pixel/PixelCard.vue'
import PixelCardTitle from '@/components/pixel/PixelCardTitle.vue'
import PixelCardContent from '@/components/pixel/PixelCardContent.vue'
import PixelCardActions from '@/components/pixel/PixelCardActions.vue'
import PixelInput from '@/components/pixel/PixelInput.vue'
import PixelButton from '@/components/pixel/PixelButton.vue'
import PixelAlert from '@/components/pixel/PixelAlert.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'

const router = useRouter()
const authStore = useAuthStore()

const email = ref<string>('')
const password = ref<string>('')
const errorMessage = ref<string>('')
const isSubmitting = ref<boolean>(false)

async function handleLogin(): Promise<void> {
  errorMessage.value = ''
  if (!email.value || !password.value) {
    errorMessage.value = 'Please enter both email and password.'
    return
  }

  isSubmitting.value = true
  try {
    const success: boolean = await authStore.login(email.value, password.value)
    if (success) {
      if (authStore.userRole === 'admin') {
        router.push('/admin')
      } else if (authStore.userRole === 'mentor') {
        router.push('/mentor')
      } else {
        router.push('/student')
      }
    } else {
      errorMessage.value = 'Invalid email or password.'
    }
  } catch (err: unknown) {
    errorMessage.value = err instanceof Error ? err.message : 'An error occurred during login.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <PixelCard class="auth-card">
      <PixelCardTitle class="auth-title-container">
        <div class="auth-header">
          <PixelSprite name="sword" :size="36" class="auth-brand-sprite" />
          <h2 class="auth-title">ZERO1</h2>
          <span class="auth-subtitle">Tactical Coding Guild</span>
        </div>
      </PixelCardTitle>

      <PixelCardContent>
        <form class="auth-form" @submit.prevent="handleLogin">
          <PixelAlert v-if="errorMessage" color="danger">
            {{ errorMessage }}
          </PixelAlert>

          <PixelInput
            v-model="email"
            label="Email Address"
            type="email"
            placeholder="student@dept.edu"
            required
          />

          <PixelInput
            v-model="password"
            label="Password"
            type="password"
            placeholder="Enter password"
            required
          />

          <PixelCardActions class="auth-actions">
            <PixelButton
              type="submit"
              color="primary"
              size="large"
              block
              :loading="isSubmitting"
              icon="login"
            >
              Enter Guild
            </PixelButton>
          </PixelCardActions>
        </form>
      </PixelCardContent>
    </PixelCard>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1.5rem;
  background-color: var(--pixel-bg);
}

.auth-card {
  width: 100%;
  max-width: 440px;
}

.auth-title-container {
  display: flex;
  justify-content: center;
  padding: 20px 16px;
}

.auth-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  width: 100%;
  gap: 6px;
}

.auth-brand-sprite {
  margin-bottom: 4px;
}

.auth-title {
  margin: 0;
  font-family: var(--font-pixel);
  font-size: 1.6rem;
  letter-spacing: 0.05em;
  color: var(--pixel-text);
}

.auth-subtitle {
  font-size: 0.85rem;
  color: var(--pixel-text-muted);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.auth-actions {
  padding: 0;
  margin-top: 0.5rem;
  background: transparent;
  border-top: none;
}
</style>
