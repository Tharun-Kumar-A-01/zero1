<script setup lang="ts">
import { computed } from 'vue'
import PixelButton from './PixelButton.vue'
import PixelIcon from './PixelIcon.vue'

interface Props {
  modelValue?: number
  pages?: number
  visiblePages?: number
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: 1,
  pages: 1,
  visiblePages: 5,
})

const emit = defineEmits<{
  (e: 'update:modelValue', page: number): void
}>()

const displayedPages = computed(() => {
  const current = props.modelValue || 1
  const total = props.pages || 1
  const max = props.visiblePages || 5

  if (total <= max) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  let start = Math.max(1, current - Math.floor(max / 2))
  let end = start + max - 1

  if (end > total) {
    end = total
    start = Math.max(1, end - max + 1)
  }

  const list: number[] = []
  for (let p = start; p <= end; p++) {
    list.push(p)
  }
  return list
})

const selectPage = (p: number) => {
  if (p < 1 || p > (props.pages || 1)) return
  emit('update:modelValue', p)
}
</script>

<template>
  <div class="pixel-pagination">
    <PixelButton
      color="secondary"
      size="small"
      :disabled="modelValue <= 1"
      @click="selectPage(modelValue - 1)"
    >
      <PixelIcon name="chevron-left" :size="12" />
    </PixelButton>

    <PixelButton
      v-for="p in displayedPages"
      :key="p"
      :color="p === modelValue ? 'primary' : 'secondary'"
      size="small"
      @click="selectPage(p)"
    >
      {{ p }}
    </PixelButton>

    <PixelButton
      color="secondary"
      size="small"
      :disabled="modelValue >= pages"
      @click="selectPage(modelValue + 1)"
    >
      <PixelIcon name="chevron-right" :size="12" />
    </PixelButton>
  </div>
</template>

<style scoped>
.pixel-pagination {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
</style>
