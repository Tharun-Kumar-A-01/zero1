<script setup lang="ts">
import { computed } from 'vue'
import PixelIcon from './PixelIcon.vue'

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
}

const props = withDefaults(defineProps<Props>(), {
  options: () => [],
  disabled: false,
  required: false,
  error: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: any): void
  (e: 'change', event: Event): void
}>()

interface NormalizedOption {
  value: any
  text: string
}

const normalizedOptions = computed<NormalizedOption[]>(() => {
  return props.options.map((opt) => {
    if (typeof opt === 'object' && opt !== null) {
      const val = props.valueBy ? opt[props.valueBy] : (opt.value ?? opt.id ?? opt)
      const txt = props.textBy ? opt[props.textBy] : (opt.label ?? opt.text ?? opt.name ?? String(val))
      return { value: val, text: String(txt) }
    }
    return { value: opt, text: String(opt) }
  })
})

const handleChange = (e: Event) => {
  const target = e.target as HTMLSelectElement
  const rawVal = target.value

  // Try matching original option value by string comparison
  const matched = normalizedOptions.value.find((opt) => String(opt.value) === rawVal)
  const finalVal = matched ? matched.value : rawVal

  emit('update:modelValue', finalVal)
  emit('change', e)
}

const errorMessage = computed(() => {
  if (Array.isArray(props.errorMessages)) {
    return props.errorMessages.join(', ')
  }
  return props.errorMessages || ''
})
</script>

<template>
  <div :class="['pixel-select-wrapper', { 'pixel-select--error': error || !!errorMessage, 'pixel-select--disabled': disabled }]">
    <label v-if="label" class="pixel-select-label">
      {{ label }}
      <span v-if="required" class="required-star">*</span>
    </label>

    <div class="pixel-select-container">
      <select
        :value="String(modelValue ?? '')"
        :disabled="disabled"
        :required="required"
        class="pixel-select-native"
        @change="handleChange"
      >
        <option v-if="placeholder" value="" disabled :selected="modelValue === undefined || modelValue === ''">
          {{ placeholder }}
        </option>
        <option
          v-for="opt in normalizedOptions"
          :key="String(opt.value)"
          :value="String(opt.value)"
        >
          {{ opt.text }}
        </option>
      </select>

      <span class="pixel-select-arrow">
        <PixelIcon name="chevron-down" :size="12" />
      </span>
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
}

.required-star {
  color: var(--pixel-btn-danger-bg);
}

.pixel-select-container {
  position: relative;
  display: flex;
  align-items: center;
  background-color: var(--pixel-bg-alt);
  border: 2px solid var(--pixel-border);
  box-shadow: inset 0 2px 0 0 rgba(0, 0, 0, 0.4);
  border-radius: 2px;
  transition: border-color 0.1s ease, box-shadow 0.1s ease;
}

.pixel-select-container:focus-within {
  border-color: var(--pixel-btn-primary-hover);
  box-shadow: inset 0 2px 0 0 rgba(0, 0, 0, 0.4), 0 0 0 1px var(--pixel-btn-primary-border);
}

.pixel-select-native {
  width: 100%;
  appearance: none;
  -webkit-appearance: none;
  background: transparent;
  border: none;
  outline: none;
  padding: 8px 30px 8px 10px;
  color: var(--pixel-text);
  font-family: var(--font-body);
  font-size: 13px;
  cursor: pointer;
}

.pixel-select-native option {
  background-color: var(--pixel-surface);
  color: var(--pixel-text);
}

.pixel-select-arrow {
  position: absolute;
  right: 10px;
  pointer-events: none;
  display: flex;
  align-items: center;
  color: var(--pixel-text-muted);
}

.pixel-select--error .pixel-select-container {
  border-color: var(--pixel-btn-danger-bg);
}

.pixel-select-error-msg {
  font-family: var(--font-body);
  font-size: 11px;
  color: #ff6b6b;
  margin-top: 2px;
}

.pixel-select--disabled {
  opacity: 0.6;
}
.pixel-select--disabled .pixel-select-native {
  cursor: not-allowed;
}
</style>
