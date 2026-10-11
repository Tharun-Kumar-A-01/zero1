<script setup lang="ts">
import { computed } from 'vue'

interface Props {
	modelValue?: string
	label?: string
	placeholder?: string
	disabled?: boolean
	readonly?: boolean
	required?: boolean
	rows?: number | string
	autosize?: boolean
	error?: boolean
	errorMessages?: string | string[]
}

const props = withDefaults(defineProps<Props>(), {
	modelValue: '',
	rows: 4,
	disabled: false,
	readonly: false,
	required: false,
	autosize: false,
	error: false,
})

const emit = defineEmits<{
	(e: 'update:modelValue', value: string): void
	(e: 'input', event: Event): void
	(e: 'change', event: Event): void
}>()

const handleInput = (event: Event) => {
	const target = event.target as HTMLTextAreaElement
	emit('update:modelValue', target.value)
	emit('input', event)
}

const errorMessage = computed(() => {
	if (Array.isArray(props.errorMessages)) {
		return props.errorMessages.join(', ')
	}
	return props.errorMessages || ''
})
</script>

<template>
	<div
		:class="[
			'pixel-textarea-wrapper',
			{
				'pixel-textarea--error': error || !!errorMessage,
				'pixel-textarea--disabled': disabled,
			},
		]"
	>
		<label v-if="label" class="pixel-textarea-label">
			{{ label }}
			<span v-if="required" class="required-star">*</span>
		</label>

		<div class="pixel-textarea-container">
			<textarea
				:value="modelValue"
				:placeholder="placeholder"
				:disabled="disabled"
				:readonly="readonly"
				:required="required"
				:rows="rows"
				class="pixel-textarea-field"
				@input="handleInput"
				@change="$emit('change', $event)"
			/>
		</div>

		<div v-if="errorMessage" class="pixel-textarea-error-msg">
			{{ errorMessage }}
		</div>
	</div>
</template>

<style scoped>
.pixel-textarea-wrapper {
	display: flex;
	flex-direction: column;
	gap: 4px;
	width: 100%;
}

.pixel-textarea-label {
	font-family: var(--font-pixel);
	font-size: 11px;
	text-transform: uppercase;
	letter-spacing: 0.05em;
	color: var(--pixel-text-muted);
}

.required-star {
	color: var(--pixel-btn-danger-bg);
}

.pixel-textarea-container {
	display: flex;
	background-color: var(--pixel-bg-alt);
	border: 2px solid var(--pixel-border);
	box-shadow: inset 0 2px 0 0 rgba(0, 0, 0, 0.4);
	border-radius: 2px;
	padding: 8px;
	transition:
		border-color 0.1s ease,
		box-shadow 0.1s ease;
}

.pixel-textarea-container:focus-within {
	border-color: var(--pixel-btn-primary-hover);
	box-shadow:
		inset 0 2px 0 0 rgba(0, 0, 0, 0.4),
		0 0 0 1px var(--pixel-btn-primary-border);
}

.pixel-textarea-field {
	width: 100%;
	background: transparent;
	border: none;
	outline: none;
	color: var(--pixel-text);
	font-family: var(--font-mono);
	font-size: 13px;
	line-height: 1.5;
	resize: vertical;
}

.pixel-textarea-field::placeholder {
	color: var(--pixel-text-dim);
}

.pixel-textarea--error .pixel-textarea-container {
	border-color: var(--pixel-btn-danger-bg);
}

.pixel-textarea-error-msg {
	font-family: var(--font-body);
	font-size: 11px;
	color: #ff6b6b;
	margin-top: 2px;
}

.pixel-textarea--disabled {
	opacity: 0.6;
}
.pixel-textarea--disabled .pixel-textarea-field {
	cursor: not-allowed;
}
</style>
