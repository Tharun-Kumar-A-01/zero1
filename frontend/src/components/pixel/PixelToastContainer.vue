<script setup lang="ts">
import { usePixelToast } from './usePixelToast'
import PixelIcon from './PixelIcon.vue'

const { toasts, close } = usePixelToast()
</script>

<template>
	<div class="pixel-toast-container" aria-live="polite">
		<TransitionGroup name="pixel-toast-list">
			<div
				v-for="toast in toasts"
				:key="toast.id"
				:class="['pixel-toast', `pixel-toast--${toast.color}`]"
			>
				<div class="pixel-toast__body">
					<div v-if="toast.title" class="pixel-toast__title">
						{{ toast.title }}
					</div>
					<div class="pixel-toast__message">
						{{ toast.message }}
					</div>
				</div>

				<button
					type="button"
					class="pixel-toast__close"
					aria-label="Close notification"
					@click="close(toast.id)"
				>
					<PixelIcon name="cross" :size="12" />
				</button>
			</div>
		</TransitionGroup>
	</div>
</template>

<style scoped>
.pixel-toast-container {
	position: fixed;
	top: 20px;
	right: 20px;
	z-index: 10000;
	display: flex;
	flex-direction: column;
	gap: 10px;
	max-width: 380px;
	pointer-events: none;
}

.pixel-toast {
	pointer-events: auto;
	display: flex;
	align-items: flex-start;
	gap: 10px;
	padding: 12px 14px;
	background-color: var(--pixel-surface);
	border: 2px solid var(--pixel-border);
	box-shadow:
		0 4px 0 0 var(--pixel-border-dark),
		0 8px 20px rgba(0, 0, 0, 0.4);
	border-radius: 3px;
	font-family: var(--font-body);
	font-size: 13px;
	color: var(--pixel-text);
}

.pixel-toast__body {
	flex: 1 1 auto;
	display: flex;
	flex-direction: column;
	gap: 2px;
}

.pixel-toast__title {
	font-family: var(--font-pixel);
	font-size: 12px;
	text-transform: uppercase;
	letter-spacing: 0.04em;
}

.pixel-toast__close {
	background: none;
	border: none;
	color: var(--pixel-text-dim);
	cursor: pointer;
	padding: 2px;
	display: flex;
	align-items: center;
}

.pixel-toast__close:hover {
	color: var(--pixel-text);
}

.pixel-toast--success {
	border-color: var(--pixel-btn-success-bg);
	background-color: #172b1d;
	color: #a7f3d0;
}

.pixel-toast--danger {
	border-color: var(--pixel-btn-danger-bg);
	background-color: #311515;
	color: #fecaca;
}

.pixel-toast--warning {
	border-color: var(--pixel-btn-warning-bg);
	background-color: #2e1d0f;
	color: #fed7aa;
}

.pixel-toast--info {
	border-color: var(--pixel-btn-info-bg);
	background-color: #112638;
	color: #bae6fd;
}

.pixel-toast--primary {
	border-color: var(--pixel-btn-primary-bg);
	background-color: #241638;
	color: #e9d5ff;
}

/* Animations */
.pixel-toast-list-enter-active,
.pixel-toast-list-leave-active {
	transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.pixel-toast-list-enter-from {
	opacity: 0;
	transform: translateX(40px) scale(0.9);
}

.pixel-toast-list-leave-to {
	opacity: 0;
	transform: translateY(-20px);
}
</style>
