<script setup lang="ts">
import { inject, computed, type ComputedRef } from 'vue'

interface Props {
	name: string | number
	disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
	disabled: false,
})

interface TabsContext {
	activeTab: ComputedRef<string | number | undefined>
	selectTab: (name: string | number) => void
}

const context = inject<TabsContext>('pixelTabsContext')

const isActive = computed(() => {
	return context?.activeTab.value === props.name
})

const handleClick = () => {
	if (props.disabled) return
	context?.selectTab(props.name)
}
</script>

<template>
	<button
		type="button"
		:class="['pixel-tab', { 'pixel-tab--active': isActive, 'pixel-tab--disabled': disabled }]"
		:disabled="disabled"
		@click="handleClick"
	>
		<slot />
	</button>
</template>

<style scoped>
.pixel-tab {
	display: inline-flex;
	align-items: center;
	gap: 8px;
	padding: 8px 16px;
	font-family: var(--font-pixel);
	font-size: 12px;
	text-transform: uppercase;
	letter-spacing: 0.04em;
	background-color: var(--pixel-surface-alt);
	color: var(--pixel-text-muted);
	border: 2px solid var(--pixel-border);
	border-bottom: none;
	border-radius: 4px 4px 0 0;
	cursor: pointer;
	user-select: none;
	transition:
		color 0.1s ease,
		background-color 0.1s ease;
	position: relative;
	z-index: 1;
}

.pixel-tab:hover:not(.pixel-tab--disabled) {
	color: var(--pixel-text);
	background-color: var(--pixel-surface);
}

.pixel-tab--active {
	background-color: var(--pixel-tab-active-bg, var(--pixel-bg));
	color: #ffffff;
	border-color: var(--pixel-border);
	border-top: 2px solid var(--pixel-btn-primary-bg);
	border-bottom: 2px solid var(--pixel-tab-active-bg, var(--pixel-bg));
	margin-bottom: -2px;
	z-index: 2;
}

.pixel-tab--disabled {
	opacity: 0.5;
	cursor: not-allowed;
}
</style>
