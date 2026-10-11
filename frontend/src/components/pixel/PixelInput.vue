<script setup lang="ts">
import { computed } from 'vue'
import PixelIcon from './PixelIcon.vue'

interface Props {
  modelValue?: string | number
  label?: string
  placeholder?: string
  type?: string
  disabled?: boolean
  readonly?: boolean
  required?: boolean
  clearable?: boolean
  min?: number | string
  max?: number | string
  step?: number | string
  error?: boolean
  errorMessages?: string | string[]
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  type: 'text',
  disabled: false,
  readonly: false,
  required: false,
  clearable: false,
  error: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | number): void
  (e: 'input', event: Event): void
  (e: 'change', event: Event): void
  (e: 'clear'): void
}>()

const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  const val = props.type === 'number' ? (target.value === '' ? '' : Number(target.value)) : target.value
  emit('update:modelValue', val)
  emit('input', event)
}

const handleClear = () => {
  emit('update:modelValue', '')
  emit('clear')
}

const errorMessage = computed(() => {
  if (Array.isArray(props.errorMessages)) {
    return props.errorMessages.join(', ')
  }
  return props.errorMessages || ''
})
</script>

<template>
  <div :class="['pixel-input-wrapper', { 'pixel-input--error': error || !!errorMessage, 'pixel-input--disabled': disabled }]">
    <label v-if="label" class="pixel-input-label">
      {{ label }}
      <span v-if="required" class="required-star">*</span>
    </label>

    <div class="pixel-input-container">
      <div v-if="$slots.prependInner" class="pixel-input-slot prepend">
        <slot name="prependInner" />
      </div>

      <input
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :required="required"
        :min="min"
        :max="max"
        :step="step"
        class="pixel-input-field"
        @input="handleInput"
        @change="$emit('change', $event)"
      />

      <button
        v-if="clearable && modelValue && !disabled && !readonly"
        type="button"
        class="pixel-input-clear-btn"
        aria-label="Clear"
        @click="handleClear"
      >
        <PixelIcon name="cross" :size="12" />
      </button>

      <div v-if="$slots.appendInner" class="pixel-input-slot append">
        <slot name="appendInner" />
      </div>
    </div>

    <div v-if="errorMessage" class="pixel-input-error-msg">
      {{ errorMessage }}
    </div>
  </div>
</template>

<style scoped>
.pixel-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}

.pixel-input-label {
  font-family: var(--font-pixel);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--pixel-text-muted);
}

.required-star {
  color: var(--pixel-btn-danger-bg);
}

.pixel-input-container {
  display: flex;
  align-items: center;
  background-color: var(--pixel-bg-alt);
  border: 2px solid var(--pixel-border);
  box-shadow: inset 0 2px 0 0 rgba(0, 0, 0, 0.4);
  border-radius: 2px;
  padding: 0 8px;
  transition: border-color 0.1s ease, box-shadow 0.1s ease;
}

.pixel-input-container:focus-within {
  border-color: var(--pixel-btn-primary-hover);
  box-shadow: inset 0 2px 0 0 rgba(0, 0, 0, 0.4), 0 0 0 1px var(--pixel-btn-primary-border);
}

.pixel-input-field {
  width: 100%;
  background: transparent;
  border: none;
  outline: none;
  padding: 8px 4px;
  color: var(--pixel-text);
  font-family: var(--font-body);
  font-size: 13px;
  line-height: 1.4;
}

.pixel-input-field::placeholder {
  color: var(--pixel-text-dim);
}

.pixel-input-slot {
  display: flex;
  align-items: center;
  color: var(--pixel-text-muted);
}

.pixel-input-slot.prepend {
  margin-right: 4px;
}

.pixel-input-slot.append {
  margin-left: 4px;
}

.pixel-input-clear-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--pixel-text-dim);
  padding: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pixel-input-clear-btn:hover {
  color: var(--pixel-text);
}

.pixel-input--error .pixel-input-container {
  border-color: var(--pixel-btn-danger-bg);
}

.pixel-input-error-msg {
  font-family: var(--font-body);
  font-size: 11px;
  color: #ff6b6b;
  margin-top: 2px;
}

.pixel-input--disabled {
  opacity: 0.6;
}
.pixel-input--disabled .pixel-input-field {
  cursor: not-allowed;
}
</style>
