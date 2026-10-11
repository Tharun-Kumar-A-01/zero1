<script setup lang="ts">
import type { RotationItem, UserItem } from '@/types'
import { formatIndianDate } from '@/utils/date'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelButton from '@/components/pixel/PixelButton.vue'

const props = defineProps<{
  activeRotation: RotationItem | null
  users: UserItem[]
}>()

const emit = defineEmits<{
  (e: 'schedule'): void
}>()

function getMentorName(userId: number): string {
  const user = props.users.find((u) => u.id === userId)
  return user ? user.name : `Mentor #${userId}`
}
</script>

<template>
  <div class="admin-header-bar">
    <div>
      <h1 class="page-title">Admin Dashboard</h1>
    </div>

    <div class="active-rotation-strip">
      <div class="rotation-meta">
        <span class="strip-label">Active Week:</span>
        <PixelBadge
          :text="activeRotation ? 'ACTIVE' : 'NO ACTIVE ROTATION'"
          :color="activeRotation ? 'success' : 'warning'"
        />
        <span v-if="activeRotation" class="rotation-details">
          <strong>{{ getMentorName(activeRotation.user_id) }}</strong>
          ({{ formatIndianDate(activeRotation.week_start_date) }} – {{ formatIndianDate(activeRotation.week_end_date) }})
        </span>
      </div>
      <PixelButton
        size="small"
        icon="calendar"
        color="secondary"
        @click="emit('schedule')"
      >
        Schedule Rotation
      </PixelButton>
    </div>
  </div>
</template>

<style scoped>
.admin-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid var(--pixel-border);
}

.page-title {
  font-family: var(--font-pixel);
  font-size: 1.75rem;
  color: var(--pixel-text);
  margin: 0;
}

.active-rotation-strip {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  background-color: var(--pixel-surface);
  border: 2px solid var(--pixel-border);
  box-shadow: 0 3px 0 0 var(--pixel-border-dark);
  border-radius: 4px;
  padding: 8px 14px;
}

.rotation-meta {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  font-size: 0.85rem;
}

.strip-label {
  font-family: var(--font-pixel);
  font-size: 11px;
  text-transform: uppercase;
  color: var(--pixel-text-dim);
}

.rotation-details {
  color: var(--pixel-text);
}
</style>
