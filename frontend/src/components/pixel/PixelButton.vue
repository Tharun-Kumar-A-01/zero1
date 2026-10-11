<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import PixelIcon from './PixelIcon.vue'
import PixelSprite from './PixelSprite.vue'

interface Props {
  color?: 'primary' | 'success' | 'danger' | 'warning' | 'info' | 'secondary'
  size?: 'small' | 'medium' | 'large'
  disabled?: boolean
  loading?: boolean
  icon?: string
  sprite?: string
  block?: boolean
  type?: 'button' | 'submit' | 'reset'
  to?: string | object
}

const props = withDefaults(defineProps<Props>(), {
  color: 'primary',
  size: 'medium',
  disabled: false,
  loading: false,
  type: 'button',
})

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()

const isLink = computed(() => !!props.to)

const handleClick = (e: MouseEvent) => {
  if (props.disabled || props.loading) {
    e.preventDefault()
    return
  }
  emit('click', e)
}
</script>

<template>
  <component
    :is="isLink ? RouterLink : 'button'"
    :to="to"
    :type="isLink ? undefined : type"
    :disabled="disabled || loading"
    :class="[
      'pixel-button',
      `pixel-button--${color}`,
      `pixel-button--${size}`,
      { 'pixel-button--block': block, 'pixel-button--disabled': disabled || loading },
    ]"
    @click="handleClick"
  >
    <span v-if="loading" class="pixel-button__spinner">
      <PixelIcon name="refresh" :size="size === 'small' ? 12 : 14" class="spin" />
    </span>
    <span v-else-if="sprite" class="pixel-button__sprite">
      <PixelSprite :name="sprite" :scale="size === 'small' ? 1 : 1.2" />
    </span>
    <span v-else-if="icon" class="pixel-button__icon">
      <PixelIcon :name="icon" :size="size === 'small' ? 12 : 14" />
    </span>

    <span v-if="$slots.default" class="pixel-button__label">
      <slot />
    </span>
  </component>
</template>

<style scoped>
.pixel-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  position: relative;
  font-family: var(--font-pixel);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  text-decoration: none;
  cursor: pointer;
  user-select: none;
  outline: none;
  border-radius: 2px;
  border-style: solid;
  border-width: 2px;
  transition: transform 0.06s ease, box-shadow 0.06s ease, filter 0.06s ease;
  line-height: 1.2;
  box-sizing: border-box;
}

/* Sizing */
.pixel-button--small {
  padding: 5px 10px;
  font-size: 11px;
  box-shadow: 0 3px 0 0 var(--btn-shade);
}
.pixel-button--medium {
  padding: 8px 16px;
  font-size: 13px;
  box-shadow: 0 4px 0 0 var(--btn-shade);
}
.pixel-button--large {
  padding: 12px 22px;
  font-size: 15px;
  box-shadow: 0 5px 0 0 var(--btn-shade);
}

.pixel-button--block {
  display: flex;
  width: 100%;
}

/* Theme Colors */
.pixel-button--primary {
  background-color: var(--pixel-btn-primary-bg);
  border-color: var(--pixel-btn-primary-border);
  color: var(--pixel-btn-primary-text);
  --btn-shade: var(--pixel-btn-primary-shade);
}
.pixel-button--primary:hover:not(.pixel-button--disabled) {
  background-color: var(--pixel-btn-primary-hover);
}

.pixel-button--success {
  background-color: var(--pixel-btn-success-bg);
  border-color: var(--pixel-btn-success-border);
  color: var(--pixel-btn-success-text);
  --btn-shade: var(--pixel-btn-success-shade);
}
.pixel-button--success:hover:not(.pixel-button--disabled) {
  background-color: var(--pixel-btn-success-hover);
}

.pixel-button--danger {
  background-color: var(--pixel-btn-danger-bg);
  border-color: var(--pixel-btn-danger-border);
  color: var(--pixel-btn-danger-text);
  --btn-shade: var(--pixel-btn-danger-shade);
}
.pixel-button--danger:hover:not(.pixel-button--disabled) {
  background-color: var(--pixel-btn-danger-hover);
}

.pixel-button--warning {
  background-color: var(--pixel-btn-warning-bg);
  border-color: var(--pixel-btn-warning-border);
  color: var(--pixel-btn-warning-text);
  --btn-shade: var(--pixel-btn-warning-shade);
}
.pixel-button--warning:hover:not(.pixel-button--disabled) {
  background-color: var(--pixel-btn-warning-hover);
}

.pixel-button--info {
  background-color: var(--pixel-btn-info-bg);
  border-color: var(--pixel-btn-info-border);
  color: var(--pixel-btn-info-text);
  --btn-shade: var(--pixel-btn-info-shade);
}
.pixel-button--info:hover:not(.pixel-button--disabled) {
  background-color: var(--pixel-btn-info-hover);
}

.pixel-button--secondary {
  background-color: var(--pixel-btn-secondary-bg);
  border-color: var(--pixel-btn-secondary-border);
  color: var(--pixel-btn-secondary-text);
  --btn-shade: var(--pixel-btn-secondary-shade);
}
.pixel-button--secondary:hover:not(.pixel-button--disabled) {
  background-color: var(--pixel-btn-secondary-hover);
}

/* Tactile Click Physics */
.pixel-button--small:active:not(.pixel-button--disabled) {
  transform: translateY(2px);
  box-shadow: 0 1px 0 0 var(--btn-shade);
}
.pixel-button--medium:active:not(.pixel-button--disabled) {
  transform: translateY(3px);
  box-shadow: 0 1px 0 0 var(--btn-shade);
}
.pixel-button--large:active:not(.pixel-button--disabled) {
  transform: translateY(4px);
  box-shadow: 0 1px 0 0 var(--btn-shade);
}

/* Disabled */
.pixel-button--disabled {
  opacity: 0.55;
  cursor: not-allowed;
  filter: grayscale(0.5);
}

.spin {
  animation: spin 1s steps(8, end) infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
