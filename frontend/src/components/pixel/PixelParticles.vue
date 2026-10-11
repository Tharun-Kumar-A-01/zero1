<script setup lang="ts">
interface Props {
  rank?: number
  aura?: 'gold' | 'silver' | 'bronze'
}

defineProps<Props>()
</script>

<template>
  <div class="pixel-particles-wrapper">
    <slot />
  </div>
</template>

<style scoped>
.pixel-particles-wrapper {
  position: relative;
  display: inline-flex;
}
</style>
