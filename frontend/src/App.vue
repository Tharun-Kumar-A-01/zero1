<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import PixelToastContainer from '@/components/pixel/PixelToastContainer.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const route = useRoute()

const isWorkspaceRoute = computed<boolean>(() => route.path.startsWith('/workspace'))

onMounted(async (): Promise<void> => {
	if (authStore.isAuthenticated && !authStore.user) {
		await authStore.fetchProfile()
	}
})
</script>

<template>
	<div
		class="app-layout"
		:class="{
			'with-sidebar': authStore.isAuthenticated,
			'in-workspace': isWorkspaceRoute,
		}"
	>
		<AppSidebar v-if="authStore.isAuthenticated" />
		<main class="app-main-content">
			<RouterView />
		</main>
		<PixelToastContainer />
	</div>
</template>

<style scoped>
.app-layout {
	display: flex;
	min-height: 100vh;
	width: 100%;
	background-color: var(--pixel-bg);
}

.app-main-content {
	flex: 1;
	display: flex;
	flex-direction: column;
	width: 100%;
	min-width: 0;
	background-color: var(--pixel-bg);
}

@media (max-width: 768px) {
	.app-layout.with-sidebar:not(.in-workspace) {
		padding-bottom: 56px;
	}
}
</style>
