<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

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
		<VaCard class="auth-card">
			<VaCardTitle class="auth-title-container">
				<div class="auth-header">
					<VaIcon name="code" size="48px" color="primary" class="auth-brand-icon" />
					<h2 class="auth-title">zero1</h2>
				</div>
			</VaCardTitle>

			<VaCardContent>
				<VaForm class="auth-form" @submit.prevent="handleLogin">
					<VaAlert v-if="errorMessage" color="danger">
						<template #icon>
							<VaIcon name="warning" />
						</template>
						{{ errorMessage }}
					</VaAlert>

					<VaInput
						v-model="email"
						label="Email Address"
						type="email"
						placeholder="student@dept.edu"
						required
					/>

					<VaInput
						v-model="password"
						label="Password"
						type="password"
						placeholder="Enter password"
						required
					/>

					<VaCardActions class="auth-actions">
						<VaButton
							type="submit"
							block
							:loading="isSubmitting"
							icon="login"
						>
							Sign In
						</VaButton>
					</VaCardActions>
				</VaForm>
			</VaCardContent>
		</VaCard>
	</div>
</template>

<style scoped>
.login-page {
	min-height: calc(100vh - 70px);
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 2rem 1.5rem;
}

.auth-card {
	width: 100%;
	max-width: 440px;
}

.auth-title-container {
	display: flex;
	justify-content: center;
}

.auth-header {
	text-align: center;
	width: 100%;
}

.auth-brand-icon {
	margin-bottom: 0.5rem;
}

.auth-title {
	margin: 0;
	font-size: 1.35rem;
	font-weight: 700;
	letter-spacing: -0.02em;
	color: var(--va-text-primary);
}

.auth-subtitle {
	color: var(--va-text-secondary);
	font-size: 0.875rem;
	margin-top: 0.5rem;
	line-height: 1.4;
}

.auth-form {
	display: flex;
	flex-direction: column;
	gap: 1.25rem;
}

.auth-actions {
	padding: 0;
	margin-top: 0.5rem;
}
</style>
