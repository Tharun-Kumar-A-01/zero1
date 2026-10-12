<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

interface Props {
	modelValue?: any
	options?: any[]
	label?: string
	placeholder?: string
	valueBy?: string
	textBy?: string
	disabled?: boolean
	required?: boolean
	error?: boolean
	errorMessages?: string | string[]
	size?: 'small' | 'medium'
}

const props = withDefaults(defineProps<Props>(), {
	options: () => [],
	disabled: false,
	required: false,
	error: false,
	size: 'medium',
})

const emit = defineEmits<{
	(e: 'update:modelValue', value: any): void
	(e: 'change', value: any): void
}>()

interface NormalizedOption {
	value: any
	text: string
}

const containerRef = ref<HTMLElement | null>(null)
const isOpen = ref<boolean>(false)

const normalizedOptions = computed<NormalizedOption[]>(() => {
	return props.options.map((opt) => {
		if (typeof opt === 'object' && opt !== null) {
			const val = props.valueBy ? opt[props.valueBy] : (opt.value ?? opt.id ?? opt)
			const txt = props.textBy
				? opt[props.textBy]
				: (opt.label ?? opt.text ?? opt.name ?? String(val))
			return { value: val, text: String(txt) }
		}
		return { value: opt, text: String(opt) }
	})
})

function isSelected(opt: NormalizedOption): boolean {
	if (props.modelValue === undefined || props.modelValue === null) return false
	return opt.value === props.modelValue || String(opt.value) === String(props.modelValue)
}

const selectedOption = computed<NormalizedOption | undefined>(() => {
	if (props.modelValue === undefined || props.modelValue === null) return undefined
	return normalizedOptions.value.find(
		(opt) => opt.value === props.modelValue || String(opt.value) === String(props.modelValue),
	)
})

const displayLabel = computed<string>(() => {
	if (selectedOption.value) {
		return selectedOption.value.text
	}
	if (props.placeholder) {
		return props.placeholder
	}
	return 'Select...'
})

const isPlaceholder = computed<boolean>(() => {
	return !selectedOption.value && Boolean(props.placeholder)
})

function toggleOpen(): void {
	if (props.disabled) return
	isOpen.value = !isOpen.value
}

function selectOption(opt: NormalizedOption): void {
	if (props.disabled) return
	emit('update:modelValue', opt.value)
	emit('change', opt.value)
	isOpen.value = false
}

function handleDocClick(e: MouseEvent): void {
	if (containerRef.value && !containerRef.value.contains(e.target as Node)) {
		isOpen.value = false
	}
}

function handleKeydown(e: KeyboardEvent): void {
	if (e.key === 'Escape' && isOpen.value) {
		isOpen.value = false
	}
}

onMounted(() => {
	document.addEventListener('click', handleDocClick)
	document.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
	document.removeEventListener('click', handleDocClick)
	document.removeEventListener('keydown', handleKeydown)
})

const errorMessage = computed(() => {
	if (Array.isArray(props.errorMessages)) {
		return props.errorMessages.join(', ')
	}
	return props.errorMessages || ''
})
</script>

<template>
	<div
		ref="containerRef"
		:class="[
			'pixel-select-wrapper',
			{
				'pixel-select--error': error || !!errorMessage,
				'pixel-select--disabled': disabled,
				'pixel-select--open': isOpen,
			},
		]"
	>
		<label v-if="label" class="pixel-select-label" @click="toggleOpen">
			{{ label }}
			<span v-if="required" class="required-star">*</span>
		</label>

		<div class="pixel-select-container">
			<!-- Tactile Pixel Dropdown Trigger -->
			<button
				type="button"
				class="pixel-select-trigger"
				:class="{
					open: isOpen,
					'is-placeholder': isPlaceholder,
					'size-small': size === 'small',
				}"
				:disabled="disabled"
				aria-haspopup="listbox"
				:aria-expanded="isOpen"
				@click="toggleOpen"
			>
				<span class="pixel-select-text">{{ displayLabel }}</span>
				<svg
					class="dropdown-chevron"
					:class="{ rotated: isOpen }"
					viewBox="0 0 20 20"
					fill="currentColor"
					aria-hidden="true"
				>
					<path
						fill-rule="evenodd"
						d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.06 1.06l-4.24 4.25a.75.75 0 01-1.06 0L5.21 8.27a.75.75 0 01.02-1.06z"
						clip-rule="evenodd"
					/>
				</svg>
			</button>

			<!-- Retro Popover Menu -->
			<Transition name="pixel-select-fade">
				<div v-if="isOpen" class="pixel-select-menu" role="listbox">
					<div v-if="normalizedOptions.length === 0" class="pixel-select-empty">
						No options available
					</div>
					<button
						v-for="opt in normalizedOptions"
						:key="String(opt.value)"
						type="button"
						role="option"
						:aria-selected="isSelected(opt)"
						class="pixel-select-item"
						:class="{ active: isSelected(opt) }"
						@mousedown.prevent
						@click="selectOption(opt)"
					>
						<span class="option-name">{{ opt.text }}</span>
						<svg
							v-if="isSelected(opt)"
							class="check-icon"
							viewBox="0 0 20 20"
							fill="currentColor"
							aria-hidden="true"
						>
							<path
								fill-rule="evenodd"
								d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
								clip-rule="evenodd"
							/>
						</svg>
					</button>
				</div>
			</Transition>
		</div>

		<div v-if="errorMessage" class="pixel-select-error-msg">
			{{ errorMessage }}
		</div>
	</div>
</template>

<style scoped>
.pixel-select-wrapper {
	display: flex;
	flex-direction: column;
	gap: 4px;
	width: 100%;
}

.pixel-select-label {
	font-family: var(--font-pixel);
	font-size: 11px;
	text-transform: uppercase;
	letter-spacing: 0.05em;
	color: var(--pixel-text-muted);
	user-select: none;
	cursor: pointer;
}

.required-star {
	color: var(--pixel-btn-danger-bg);
}

.pixel-select-container {
	position: relative;
	width: 100%;
}

.pixel-select-trigger {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.5rem;
	width: 100%;
	min-height: 36px;
	height: 36px;
	padding: 0 0.75rem;
	background: var(--pixel-surface-alt);
	color: var(--pixel-text);
	border: 2px solid var(--pixel-border);
	border-radius: 2px;
	box-shadow: 0 3px 0 0 var(--pixel-border-dark);
	font-family: var(--font-pixel);
	font-size: 11px;
	text-transform: uppercase;
	letter-spacing: 0.04em;
	cursor: pointer !important;
	user-select: none;
	text-align: left;
	transition:
		background 0.1s,
		border-color 0.1s,
		transform 0.08s,
		box-shadow 0.08s;
}

.pixel-select-trigger.size-small {
	min-height: 32px;
	height: 32px;
}

.pixel-select-trigger:hover:not(:disabled) {
	background: var(--pixel-surface-raised);
	border-color: var(--pixel-border-bright);
}

.pixel-select-trigger.open {
	border-color: var(--pixel-btn-primary-bg);
	transform: translateY(2px);
	box-shadow: 0 1px 0 0 var(--pixel-border-dark);
}

.pixel-select-trigger.is-placeholder .pixel-select-text {
	color: var(--pixel-text-dim);
}

.pixel-select-text {
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	flex: 1 1 auto;
}

.dropdown-chevron {
	width: 14px;
	height: 14px;
	color: var(--pixel-text-dim);
	transition: transform 0.15s ease;
	flex-shrink: 0;
}

.dropdown-chevron.rotated {
	transform: rotate(180deg);
}

.pixel-select-menu {
	position: absolute;
	top: calc(100% + 4px);
	left: 0;
	right: 0;
	z-index: 1000;
	min-width: 100%;
	max-height: 220px;
	overflow-y: auto;
	background: var(--pixel-surface);
	border: 2px solid var(--pixel-border);
	border-radius: 2px;
	box-shadow:
		0 4px 0 0 var(--pixel-border-dark),
		0 8px 20px rgba(0, 0, 0, 0.45);
	padding: 4px;
	display: flex;
	flex-direction: column;
	gap: 3px;
}

.pixel-select-menu::-webkit-scrollbar {
	width: 6px;
}
.pixel-select-menu::-webkit-scrollbar-track {
	background: var(--pixel-surface-alt);
}
.pixel-select-menu::-webkit-scrollbar-thumb {
	background: var(--pixel-border);
	border-radius: 2px;
}
.pixel-select-menu::-webkit-scrollbar-thumb:hover {
	background: var(--pixel-border-bright);
}

.pixel-select-item {
	display: flex;
	align-items: center;
	justify-content: space-between;
	width: 100%;
	padding: 0.45rem 0.65rem;
	background: transparent;
	border: none;
	border-radius: 2px;
	color: var(--pixel-text);
	font-family: var(--font-pixel);
	font-size: 11px;
	text-transform: uppercase;
	letter-spacing: 0.04em;
	text-align: left;
	cursor: pointer !important;
	user-select: none;
	transition:
		background 0.1s,
		color 0.1s;
	flex-shrink: 0;
}

.pixel-select-item:hover {
	background: var(--pixel-surface-raised);
	color: var(--pixel-btn-primary-text);
}

.pixel-select-item.active {
	background: var(--pixel-btn-primary-bg);
	color: var(--pixel-btn-primary-text);
}

.option-name {
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.check-icon {
	width: 14px;
	height: 14px;
	color: var(--pixel-btn-primary-text);
	flex-shrink: 0;
	margin-left: 8px;
}

.pixel-select-empty {
	padding: 0.65rem;
	font-family: var(--font-pixel);
	font-size: 11px;
	color: var(--pixel-text-dim);
	text-align: center;
	text-transform: uppercase;
}

.pixel-select--error .pixel-select-trigger {
	border-color: var(--pixel-btn-danger-bg);
}

.pixel-select-error-msg {
	font-family: var(--font-pixel);
	font-size: 10px;
	color: var(--pixel-danger);
	margin-top: 2px;
	text-transform: uppercase;
}

.pixel-select--disabled {
	opacity: 0.6;
}

.pixel-select--disabled .pixel-select-trigger {
	cursor: not-allowed !important;
}

.pixel-select-fade-enter-active,
.pixel-select-fade-leave-active {
	transition:
		opacity 0.1s ease,
		transform 0.1s ease;
}

.pixel-select-fade-enter-from,
.pixel-select-fade-leave-to {
	opacity: 0;
	transform: translateY(-4px);
}
</style>
