<template>
  <div class="pixel-card-title">
    <slot />
  </div>
</template>

<style scoped>
.pixel-card-title {
  padding: 12px 16px;
  font-family: var(--font-pixel);
  font-size: 14px;
  color: var(--pixel-text);
  border-bottom: 2px solid var(--pixel-border);
  background-color: var(--pixel-surface-alt);
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
