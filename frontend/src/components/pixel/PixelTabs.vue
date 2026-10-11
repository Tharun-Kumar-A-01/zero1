<script setup lang="ts">
import { provide, computed } from 'vue'

interface Props {
	modelValue?: string | number
}

const props = defineProps<Props>()

const emit = defineEmits<{
	(e: 'update:modelValue', value: string | number): void
}>()

const activeTab = computed(() => props.modelValue)

provide('pixelTabsContext', {
	activeTab,
	selectTab: (tabName: string | number) => {
		emit('update:modelValue', tabName)
	},
})
</script>

<template>
	<div class="pixel-tabs">
		<div class="pixel-tabs__nav">
			<slot />
		</div>
	</div>
</template>

<style scoped>
.pixel-tabs {
	width: 100%;
}

.pixel-tabs__nav {
	display: flex;
	align-items: flex-end;
	gap: 4px;
	border-bottom: 2px solid var(--pixel-border);
	position: relative;
	overflow-x: auto;
	overflow-y: hidden;
	scrollbar-width: none;
	-ms-overflow-style: none;
}

.pixel-tabs__nav::-webkit-scrollbar {
	display: none;
	width: 0;
	height: 0;
}
</style>
