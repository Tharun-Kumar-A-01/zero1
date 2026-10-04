<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import type { LeaderboardEntry } from '@/types'
import LeaderboardBanner from '@/components/leaderboard/LeaderboardBanner.vue'
import PodiumSection from '@/components/leaderboard/PodiumSection.vue'
import RankingsList from '@/components/leaderboard/RankingsList.vue'
import MyPositionDock from '@/components/leaderboard/MyPositionDock.vue'

const authStore = useAuthStore()

const isLoading = ref<boolean>(true)
const entries = ref<LeaderboardEntry[]>([])
const selectedBatch = ref<string>('2026')

const batchOptions = [
	{ label: 'Batch 2026', value: '2026' },
	{ label: 'Batch 2025', value: '2025' },
	{ label: 'Batch 2024', value: '2024' },
	{ label: 'All Batches', value: '' },
]

const myEntry = computed<LeaderboardEntry | null>(() => {
	if (!authStore.user) return null
	return entries.value.find((e) => e.student_id === authStore.user?.id) || null
})

async function fetchLeaderboard(): Promise<void> {
	isLoading.value = true
	try {
		const endpoint = selectedBatch.value ? `/student/leaderboard?year_batch=${selectedBatch.value}` : '/student/leaderboard'
		const res = await api.get<LeaderboardEntry[]>(endpoint)
		if (res.success && res.data) {
			entries.value = res.data
		}
	} catch {
		// Silent error
	} finally {
		isLoading.value = false
	}
}

onMounted(async (): Promise<void> => {
	if (authStore.user?.year_batch) {
		selectedBatch.value = authStore.user.year_batch
	}
	await fetchLeaderboard()
})
</script>

<template>
	<div class="leaderboard-page">
		<LeaderboardBanner
			v-model:selectedBatch="selectedBatch"
			:batchOptions="batchOptions"
			@change="fetchLeaderboard"
		/>

		<!-- Top 3 Podium Cards -->
		<PodiumSection :entries="entries" />

		<!-- Ranked Peer List -->
		<RankingsList
			:entries="entries"
			:currentUserId="authStore.user?.id"
		/>

		<!-- Sticky Bottom "Your Position" Ribbon -->
		<MyPositionDock
			v-if="myEntry && authStore.userRole === 'student'"
			:entry="myEntry"
		/>
	</div>
</template>

<style scoped>
.leaderboard-page {
	max-width: 1200px;
	margin: 0 auto;
	padding: 1.5rem;
	width: 100%;
	padding-bottom: 5rem;
}
</style>
