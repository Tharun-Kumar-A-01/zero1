<script setup lang="ts">
import { ref } from 'vue'
import PixelIcon from './PixelIcon.vue'

interface Props {
	color?: 'primary' | 'success' | 'danger' | 'warning' | 'info' | string
	title?: string
	closeable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
	color: 'info',
	closeable: false,
})

const visible = ref(true)

const emit = defineEmits<{
	(e: 'close'): void
}>()

const handleClose = () => {
	visible.value = false
	emit('close')
}
</script>

<template>
	<div v-if="visible" :class="['pixel-alert', `pixel-alert--${color}`]">
		<div v-if="$slots.icon" class="pixel-alert__icon">
			<slot name="icon" />
		</div>

		<div class="pixel-alert__content">
			<div v-if="title || $slots.title" class="pixel-alert__title">
				<slot name="title">{{ title }}</slot>
			</div>
			<div class="pixel-alert__body">
				<slot />
			</div>
		</div>

		<button
			v-if="closeable"
			type="button"
			class="pixel-alert__close"
			aria-label="Dismiss alert"
			@click="handleClose"
		>
			<PixelIcon name="cross" :size="12" />
		</button>
	</div>
</template>

<style scoped>
.pixel-alert {
	display: flex;
	align-items: flex-start;
	gap: 12px;
	padding: 12px 14px;
	border-radius: 3px;
	border: 2px solid var(--pixel-border);
	box-shadow: 0 3px 0 0 rgba(0, 0, 0, 0.4);
	font-family: var(--font-body);
	font-size: 13px;
	line-height: 1.4;
	position: relative;
}

.pixel-alert__icon {
	flex-shrink: 0;
	display: flex;
	align-items: center;
	padding-top: 2px;
}

.pixel-alert__content {
	flex: 1 1 auto;
	display: flex;
	flex-direction: column;
	gap: 4px;
}

.pixel-alert__title {
	font-family: var(--font-pixel);
	font-size: 12px;
	text-transform: uppercase;
	letter-spacing: 0.04em;
}

.pixel-alert__close {
	background: none;
	border: none;
	color: inherit;
	opacity: 0.7;
	cursor: pointer;
	padding: 2px;
	display: flex;
	align-items: center;
}

.pixel-alert__close:hover {
	opacity: 1;
}

.pixel-alert--danger {
	background-color: rgba(184, 51, 51, 0.15);
	border-color: var(--pixel-btn-danger-bg);
	color: var(--pixel-danger);
}

.pixel-alert--warning {
	background-color: rgba(201, 119, 22, 0.15);
	border-color: var(--pixel-btn-warning-bg);
	color: var(--pixel-warning);
}

.pixel-alert--success {
	background-color: rgba(40, 135, 70, 0.15);
	border-color: var(--pixel-btn-success-bg);
	color: var(--pixel-success);
}

.pixel-alert--info {
	background-color: rgba(29, 123, 175, 0.15);
	border-color: var(--pixel-btn-info-bg);
	color: var(--pixel-info);
}

.pixel-alert--primary {
	background-color: rgba(90, 50, 163, 0.15);
	border-color: var(--pixel-btn-primary-bg);
	color: var(--pixel-primary);
}
</style>
