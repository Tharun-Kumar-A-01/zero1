<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(async (): Promise<void> => {
	if (authStore.isAuthenticated && !authStore.user) {
		await authStore.fetchProfile()
	}
})
</script>

<template>
	<div class="app-layout" :class="{ 'with-sidebar': authStore.isAuthenticated }">
		<AppSidebar v-if="authStore.isAuthenticated" />
		<main class="app-main-content">
			<RouterView />
		</main>
	</div>
</template>

<style scoped>
.app-layout {
	display: flex;
	min-height: 100vh;
	width: 100%;
}

.app-main-content {
	flex: 1;
	display: flex;
	flex-direction: column;
	width: 100%;
	min-width: 0;
	background-color: var(--va-background-primary);
}
</style>
