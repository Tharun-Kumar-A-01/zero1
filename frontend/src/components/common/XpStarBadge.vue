<script setup lang="ts">
import PixelSprite from '@/components/pixel/PixelSprite.vue'

withDefaults(
  defineProps<{
    points: number | string
    size?: 'small' | 'medium' | 'large'
    showLabel?: boolean
  }>(),
  {
    size: 'medium',
    showLabel: true,
  },
)
</script>

<template>
  <span class="xp-stat" :class="`size-${size}`">
    <PixelSprite
      name="star"
      :size="size === 'small' ? 14 : size === 'large' ? 20 : 16"
      class="xp-star-sprite"
    />
    <span class="xp-val">{{ points }}</span>
    <span v-if="showLabel" class="xp-unit">XP</span>
  </span>
</template>

<style scoped>
.xp-stat {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-family: var(--font-pixel);
  font-weight: normal;
  color: #fbbf24;
  line-height: 1;
  vertical-align: middle;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.size-small {
  font-size: 0.8rem;
}
.size-medium {
  font-size: 0.95rem;
}
.size-large {
  font-size: 1.15rem;
}

.xp-star-sprite {
  flex-shrink: 0;
  filter: drop-shadow(0 0 4px rgba(251, 191, 36, 0.6));
}

.xp-unit {
  font-size: 0.8em;
  opacity: 0.8;
  letter-spacing: 0.05em;
  color: var(--pixel-text-muted);
}
</style>
