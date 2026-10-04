<script setup lang="ts">
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
			<h1 class="page-title">Leaderboard</h1>
		</div>

		<div class="batch-filter-wrap">
			<VaSelect
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
	border-bottom: 1px solid var(--va-background-border);
}

.page-title {
	font-size: 1.5rem;
	font-weight: 700;
	color: var(--va-text-primary);
	margin: 0;
}

.batch-filter-wrap {
	min-width: 220px;
}
</style>
