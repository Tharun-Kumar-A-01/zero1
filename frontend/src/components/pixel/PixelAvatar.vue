<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  size?: 'small' | 'medium' | 'large' | number | string
  color?: string
  src?: string
  square?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium',
  color: 'primary',
  square: true,
})

const sizePx = computed(() => {
  if (typeof props.size === 'number') return `${props.size}px`
  if (props.size === 'small') return '28px'
  if (props.size === 'large') return '48px'
  if (props.size === 'medium') return '36px'
  return props.size
})

const fontSizePx = computed(() => {
  if (props.size === 'small') return '12px'
  if (props.size === 'large') return '20px'
  return '14px'
})

const bgColor = computed(() => {
  const COLOR_MAP: Record<string, string> = {
    primary: 'var(--pixel-btn-primary-bg)',
    success: 'var(--pixel-btn-success-bg)',
    danger: 'var(--pixel-btn-danger-bg)',
    warning: 'var(--pixel-btn-warning-bg)',
    info: 'var(--pixel-btn-info-bg)',
    secondary: 'var(--pixel-btn-secondary-bg)',
  }
  return COLOR_MAP[props.color] || props.color
})
</script>

<template>
  <div
    :class="['pixel-avatar', { 'pixel-avatar--rounded': !square }]"
    :style="{
      width: sizePx,
      height: sizePx,
      fontSize: fontSizePx,
      backgroundColor: bgColor,
    }"
  >
    <img v-if="src" :src="src" class="pixel-avatar__img" alt="Avatar" />
    <slot v-else />
  </div>
</template>

<style scoped>
.pixel-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-pixel);
  font-weight: bold;
  color: #fff;
  border: 2px solid var(--pixel-border);
  box-shadow: 0 2px 0 0 rgba(0, 0, 0, 0.4);
  border-radius: 4px;
  overflow: hidden;
  user-select: none;
  flex-shrink: 0;
}

.pixel-avatar--rounded {
  border-radius: 50%;
}

.pixel-avatar__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  image-rendering: pixelated;
}
</style>
