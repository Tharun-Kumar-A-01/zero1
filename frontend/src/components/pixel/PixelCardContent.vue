<template>
  <div class="pixel-card-content">
    <slot />
  </div>
</template>

<style scoped>
.pixel-card-content {
  padding: 16px;
  flex: 1 1 auto;
  font-family: var(--font-body);
  color: var(--pixel-text);
  line-height: 1.5;
}
</style>
