<script setup lang="ts">
interface Props {
  outlined?: boolean
  flat?: boolean
  color?: string
}

withDefaults(defineProps<Props>(), {
  outlined: false,
  flat: false,
})
</script>

<template>
  <div
    :class="[
      'pixel-card',
      { 'pixel-card--outlined': outlined, 'pixel-card--flat': flat },
    ]"
    :style="color ? { backgroundColor: color } : {}"
  >
    <slot />
  </div>
</template>

<style scoped>
.pixel-card {
  --pixel-tab-active-bg: var(--pixel-surface);
  background-color: var(--pixel-surface);
  border: 2px solid var(--pixel-border);
  box-shadow: 0 4px 0 0 var(--pixel-border-dark);
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: transform 0.1s ease, box-shadow 0.1s ease;
}

.pixel-card--flat {
  box-shadow: none;
}

.pixel-card--outlined {
  background-color: transparent;
  border-color: var(--pixel-border-bright);
}
</style>
