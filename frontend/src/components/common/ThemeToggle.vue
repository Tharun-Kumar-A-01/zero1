<script setup lang="ts">
import { useTheme } from '@/composables/useTheme'
import PixelIcon from '@/components/pixel/PixelIcon.vue'

interface Props {
	size?: 'small' | 'medium'
	showLabel?: boolean
}

const props = withDefaults(defineProps<Props>(), {
	size: 'small',
	showLabel: false,
})

const { isDark, toggleTheme } = useTheme()
</script>

<template>
	<button
		type="button"
		class="pixel-theme-toggle"
		:class="[`toggle--${props.size}`]"
		:title="isDark ? 'Switch to light theme' : 'Switch to dark theme'"
		:aria-label="isDark ? 'Switch to light theme' : 'Switch to dark theme'"
		@click="toggleTheme"
	>
		<!-- When in dark theme: moon crescent icon. When in light theme: sun icon -->
		<PixelIcon
			:name="isDark ? 'moon' : 'sun'"
			:size="props.size === 'small' ? 14 : 16"
			class="theme-icon"
		/>
		<span v-if="props.showLabel" class="toggle-label">
			{{ isDark ? 'Dark' : 'Light' }}
		</span>
	</button>
</template>

<style scoped>
.pixel-theme-toggle {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 6px;
	background-color: var(--pixel-btn-secondary-bg);
	border: 2px solid var(--pixel-btn-secondary-border);
	box-shadow: 0 3px 0 0 var(--pixel-btn-secondary-shade);
	color: var(--pixel-btn-secondary-text);
	font-family: var(--font-pixel);
	font-size: 11px;
	letter-spacing: 0.04em;
	text-transform: uppercase;
	cursor: pointer;
	user-select: none;
	transition: background-color 0.1s ease, transform 0.08s ease, box-shadow 0.08s ease;
	border-radius: 0;
	padding: 0;
}

.toggle--small {
	width: 32px;
	height: 32px;
}

.toggle--medium {
	width: 38px;
	height: 38px;
}

.pixel-theme-toggle:hover {
	background-color: var(--pixel-btn-secondary-hover);
}

.pixel-theme-toggle:active {
	transform: translateY(2px);
	box-shadow: 0 1px 0 0 var(--pixel-btn-secondary-shade);
}

.theme-icon {
	color: inherit;
	flex-shrink: 0;
	pointer-events: none;
}

.toggle-label {
	font-family: var(--font-pixel);
	line-height: 1;
}
</style>
