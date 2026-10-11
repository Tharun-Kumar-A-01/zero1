<script setup lang="ts">
import { provide, computed } from 'vue'

interface Props {
  modelValue?: string | number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | number): void
}>()

const activeTab = computed(() => props.modelValue)

provide('pixelTabsContext', {
  activeTab,
  selectTab: (tabName: string | number) => {
    emit('update:modelValue', tabName)
  },
})
</script>

<template>
  <div class="pixel-tabs">
    <div class="pixel-tabs__nav">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.pixel-tabs {
  width: 100%;
}

.pixel-tabs__nav {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  border-bottom: 2px solid var(--pixel-border);
  overflow-x: auto;
}
</style>
