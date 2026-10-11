<script setup lang="ts">
import PixelSelect from '@/components/pixel/PixelSelect.vue'

defineProps<{
	selectedBatch: string
	batchOptions: Array<{ label: string; value: string }>
}>()

const emit = defineEmits<{
	(e: 'update:selectedBatch', val: string): void
	(e: 'change'): void
}>()

function handleChange(val: string): void {
	emit('update:selectedBatch', val)
	emit('change')
}
</script>

<template>
	<div class="leaderboard-header-bar">
		<div>
			<h1 class="page-title">Hall of Fame</h1>
		</div>

		<div class="batch-filter-wrap">
			<PixelSelect
				:model-value="selectedBatch"
				:options="batchOptions"
				label="Filter Cohort Year"
				value-by="value"
				text-by="label"
				class="batch-dropdown"
				@update:model-value="handleChange"
			/>
		</div>
	</div>
</template>

<style scoped>
.leaderboard-header-bar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	flex-wrap: wrap;
	gap: 1rem;
	margin-bottom: 1.5rem;
	padding-bottom: 1rem;
	border-bottom: 2px solid var(--pixel-border);
}

.page-title {
	font-family: var(--font-pixel);
	font-size: 1.75rem;
	letter-spacing: -0.01em;
	color: var(--pixel-text);
	margin: 0;
}

.batch-filter-wrap {
	min-width: 220px;
}
</style>
