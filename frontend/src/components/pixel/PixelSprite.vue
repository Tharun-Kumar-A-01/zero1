<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  name?: string
  col?: number
  row?: number
  scale?: number
  size?: number // if size is specified, scale is calculated (size / 16)
}

const props = withDefaults(defineProps<Props>(), {
  col: 0,
  row: 0,
  scale: 1,
})

const SPRITE_MAP: Record<string, { col: number; row: number }> = {
  flame: { col: 1, row: 0 },
  fire: { col: 1, row: 0 },
  ember: { col: 0, row: 0 },
  potion: { col: 2, row: 0 },
  gem: { col: 3, row: 0 },
  sword: { col: 4, row: 0 },
  blade: { col: 5, row: 0 },
  dagger: { col: 6, row: 0 },
  wand: { col: 7, row: 0 },
  crown: { col: 0, row: 1 },
  trophy: { col: 0, row: 1 },
  gold: { col: 0, row: 1 },
  coin: { col: 1, row: 1 },
  silver: { col: 2, row: 1 },
  star: { col: 3, row: 1 },
  shield: { col: 0, row: 2 },
  bronze: { col: 0, row: 2 },
  heart: { col: 0, row: 3 },
  key: { col: 1, row: 3 },
  chest: { col: 2, row: 3 },
  book: { col: 4, row: 3 },
  scroll: { col: 5, row: 3 },
}

const effectiveScale = computed(() => {
  if (props.size) {
    return props.size / 16
  }
  return props.scale
})

const coords = computed<{ col: number; row: number }>(() => {
  if (props.name) {
    const found = SPRITE_MAP[props.name.toLowerCase()]
    if (found) return found
  }
  return { col: props.col, row: props.row }
})

const spriteStyle = computed(() => {
  const s = effectiveScale.value
  const width = 16 * s
  const height = 16 * s
  const bgSize = 200 * s
  const posX = -coords.value.col * 16 * s
  const posY = -coords.value.row * 16 * s

  return {
    width: `${width}px`,
    height: `${height}px`,
    backgroundSize: `${bgSize}px ${bgSize}px`,
    backgroundPosition: `${posX}px ${posY}px`,
  }
})
</script>

<template>
  <span class="pixel-sprite" :style="spriteStyle" />
</template>

<style scoped>
.pixel-sprite {
  display: inline-block;
  vertical-align: middle;
  background-image: url('@/assets/images/icons_8x8_transparent.png');
  background-repeat: no-repeat;
  image-rendering: pixelated;
  image-rendering: crisp-edges;
  flex-shrink: 0;
}
</style>
