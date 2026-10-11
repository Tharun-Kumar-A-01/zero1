<script setup lang="ts">
import PixelSprite from './PixelSprite.vue'

interface Props {
  active?: boolean
  ignite?: boolean
  size?: number
}

withDefaults(defineProps<Props>(), {
  active: true,
  ignite: false,
  size: 32,
})
</script>

<template>
  <div
    class="pixel-flame-container"
    :style="{ width: `${size}px`, height: `${size}px` }"
  >
    <div :class="['pixel-flame-sprite-wrap', { 'flame-flicker': active }]">
      <PixelSprite name="flame" :size="size" />
    </div>
  </div>
</template>

<style scoped>
.pixel-flame-container {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.pixel-flame-sprite-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s ease;
}

.flame-flicker {
  animation: flameBounce 1.4s infinite ease-in-out alternate;
}

@keyframes flameBounce {
  0% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-1px) scale(1.02);
  }
  100% {
    transform: translateY(0) scale(0.98);
  }
}
</style>
