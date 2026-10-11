<script setup lang="ts">
import { computed } from 'vue'

interface Props {
	modelValue?: number
	color?: 'primary' | 'success' | 'danger' | 'warning' | 'info' | string
	showPercent?: boolean
	size?: 'small' | 'medium' | 'large'
}

const props = withDefaults(defineProps<Props>(), {
	modelValue: 0,
	color: 'primary',
	showPercent: false,
	size: 'medium',
})

const clampedPercent = computed(() => {
	return Math.max(0, Math.min(100, props.modelValue || 0))
})

const barColorStyle = computed(() => {
	const COLOR_MAP: Record<string, { bg: string; border: string }> = {
		primary: { bg: 'var(--pixel-btn-primary-bg)', border: 'var(--pixel-btn-primary-hover)' },
		success: { bg: 'var(--pixel-btn-success-bg)', border: 'var(--pixel-btn-success-hover)' },
		danger: { bg: 'var(--pixel-btn-danger-bg)', border: 'var(--pixel-btn-danger-hover)' },
		warning: { bg: 'var(--pixel-btn-warning-bg)', border: 'var(--pixel-btn-warning-hover)' },
		info: { bg: 'var(--pixel-btn-info-bg)', border: 'var(--pixel-btn-info-hover)' },
	}

	const mapped = COLOR_MAP[props.color]
	if (mapped) {
		return {
			backgroundColor: mapped.bg,
			borderTop: `2px solid ${mapped.border}`,
		}
	}

	return {
		backgroundColor: props.color,
		borderTop: '2px solid rgba(255, 255, 255, 0.4)',
	}
})
</script>

<template>
	<div :class="['pixel-progress-bar-wrapper', `pixel-progress-bar--${size}`]">
		<div class="pixel-progress-bar-track">
			<div
				class="pixel-progress-bar-fill"
				:style="{ width: `${clampedPercent}%`, ...barColorStyle }"
			/>
		</div>
		<span v-if="showPercent" class="pixel-progress-bar-text">
			{{ Math.round(clampedPercent) }}%
		</span>
	</div>
</template>

<style scoped>
.pixel-progress-bar-wrapper {
	display: flex;
	align-items: center;
	gap: 8px;
	width: 100%;
}

.pixel-progress-bar-track {
	flex: 1 1 auto;
	background-color: var(--pixel-bg-alt);
	border: 2px solid var(--pixel-border);
	box-shadow: inset 0 2px 0 0 rgba(0, 0, 0, 0.5);
	border-radius: 2px;
	overflow: hidden;
	height: 14px;
	position: relative;
}

.pixel-progress-bar--small .pixel-progress-bar-track {
	height: 10px;
}
.pixel-progress-bar--large .pixel-progress-bar-track {
	height: 20px;
}

.pixel-progress-bar-fill {
	height: 100%;
	transition: width 0.3s ease-out;
	box-sizing: border-box;
}

.pixel-progress-bar-text {
	font-family: var(--font-pixel);
	font-size: 11px;
	color: var(--pixel-text-muted);
	min-width: 36px;
	text-align: right;
}
</style>
