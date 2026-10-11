<template>
  <div class="pixel-card-actions">
    <slot />
  </div>
</template>

<style scoped>
.pixel-card-actions {
  padding: 12px 16px;
  border-top: 2px solid var(--pixel-border);
  background-color: var(--pixel-surface-alt);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}
</style>
