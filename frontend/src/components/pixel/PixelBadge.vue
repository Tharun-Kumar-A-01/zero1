<script setup lang="ts">
import { computed, useSlots } from 'vue'

interface Props {
	text?: string | number
	color?: 'primary' | 'success' | 'danger' | 'warning' | 'info' | 'secondary' | string
	dot?: boolean
	overlap?: boolean
}

const props = withDefaults(defineProps<Props>(), {
	color: 'primary',
	dot: false,
	overlap: false,
})

const slots = useSlots()
const hasDefaultSlot = computed(() => !!slots.default)

const badgeColorClass = computed(() => {
	const standardColors = ['primary', 'success', 'danger', 'warning', 'info', 'secondary']
	if (standardColors.includes(props.color)) {
		return `pixel-badge--${props.color}`
	}
	return ''
})

const customStyle = computed(() => {
	const standardColors = ['primary', 'success', 'danger', 'warning', 'info', 'secondary']
	if (!standardColors.includes(props.color)) {
		return { backgroundColor: props.color }
	}
	return {}
})
</script>

<template>
	<div v-if="hasDefaultSlot" class="pixel-badge-wrapper">
		<slot />
		<span
			:class="[
				'pixel-badge',
				'pixel-badge--floating',
				badgeColorClass,
				{ 'pixel-badge--dot': dot },
			]"
			:style="customStyle"
		>
			<template v-if="!dot">{{ text }}</template>
		</span>
	</div>
	<span
		v-else
		:class="['pixel-badge', badgeColorClass, { 'pixel-badge--dot': dot }]"
		:style="customStyle"
	>
		<slot v-if="!text" />
		<template v-else>{{ text }}</template>
	</span>
</template>

<style scoped>
.pixel-badge-wrapper {
	position: relative;
	display: inline-flex;
}

.pixel-badge {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	font-family: var(--font-pixel);
	font-size: 11px;
	line-height: 1;
	padding: 3px 6px;
	border-radius: 2px;
	border: 1px solid var(--pixel-border-dark);
	color: var(--pixel-btn-primary-text);
	letter-spacing: 0.02em;
	user-select: none;
	white-space: nowrap;
}

.pixel-badge--floating {
	position: absolute;
	top: -6px;
	right: -6px;
	z-index: 2;
}

.pixel-badge--dot {
	width: 8px;
	height: 8px;
	padding: 0;
	border-radius: 50%;
}

.pixel-badge--primary {
	background-color: var(--pixel-btn-primary-bg);
}
.pixel-badge--success {
	background-color: var(--pixel-btn-success-bg);
}
.pixel-badge--danger {
	background-color: var(--pixel-btn-danger-bg);
}
.pixel-badge--warning {
	background-color: var(--pixel-btn-warning-bg);
}
.pixel-badge--info {
	background-color: var(--pixel-btn-info-bg);
}
.pixel-badge--secondary {
	background-color: var(--pixel-btn-secondary-bg);
}
</style>
