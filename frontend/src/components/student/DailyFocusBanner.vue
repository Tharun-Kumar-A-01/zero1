<script setup lang="ts">
import type { DailyChallengeData } from '@/types'
import PixelAvatar from '@/components/pixel/PixelAvatar.vue'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'

defineProps<{
  challenge: DailyChallengeData | null
  studentName: string
}>()
</script>

<template>
  <div class="focus-header-bar">
    <div>
      <h1 class="page-title">Daily Practice</h1>
    </div>

    <!-- Status strip with tactile pixel indicators -->
    <div class="status-strip">
      <div class="status-item">
        <PixelAvatar
          size="small"
          :color="challenge?.mcq_status === 'correct' ? 'success' : 'secondary'"
        >
          <PixelIcon :name="challenge?.mcq_status === 'correct' ? 'check' : 'help'" :size="12" />
        </PixelAvatar>
        <span class="status-label">MCQ:</span>
        <PixelBadge
          :text="challenge?.mcq_status === 'correct' ? 'SOLVED (+20 XP)' : challenge?.mcq_status === 'incorrect' ? 'RETRY' : 'PENDING'"
          :color="challenge?.mcq_status === 'correct' ? 'success' : challenge?.mcq_status === 'incorrect' ? 'danger' : 'secondary'"
        />
      </div>

      <div class="strip-divider" />

      <div class="status-item">
        <PixelAvatar
          size="small"
          :color="challenge?.coding_status === 'solved' ? 'success' : 'secondary'"
        >
          <PixelIcon :name="challenge?.coding_status === 'solved' ? 'check' : 'code'" :size="12" />
        </PixelAvatar>
        <span class="status-label">Coding:</span>
        <PixelBadge
          :text="challenge?.coding_status === 'solved' ? 'PASSED (+30 XP)' : challenge?.coding_status === 'attempted_unsolved' ? 'ATTEMPTED' : 'PENDING'"
          :color="challenge?.coding_status === 'solved' ? 'success' : challenge?.coding_status === 'attempted_unsolved' ? 'warning' : 'secondary'"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.focus-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.page-title {
  font-family: var(--font-pixel);
  font-size: 1.75rem;
  letter-spacing: -0.01em;
  color: var(--pixel-text);
  margin: 0;
}

.status-strip {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  background-color: var(--pixel-surface);
  border: 2px solid var(--pixel-border);
  box-shadow: 0 3px 0 0 var(--pixel-border-dark);
  border-radius: 4px;
  padding: 6px 14px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-label {
  font-family: var(--font-pixel);
  font-size: 11px;
  text-transform: uppercase;
  color: var(--pixel-text-muted);
}

.strip-divider {
  width: 2px;
  height: 20px;
  background-color: var(--pixel-border);
}
</style>
