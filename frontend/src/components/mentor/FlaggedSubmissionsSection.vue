<script setup lang="ts">
import type { FlaggedSubmission } from '@/types'
import PixelCard from '@/components/pixel/PixelCard.vue'
import PixelCardContent from '@/components/pixel/PixelCardContent.vue'
import PixelCardActions from '@/components/pixel/PixelCardActions.vue'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelButton from '@/components/pixel/PixelButton.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'

defineProps<{
  flaggedSubmissions: FlaggedSubmission[]
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'resolve', payload: { submissionId: number; resolution: 'dismiss' | 'action' }): void
}>()
</script>

<template>
  <div class="pool-container">
    <div class="pool-header">
      <div>
        <h2 class="section-title">Flagged Submissions Queue</h2>
        <p class="section-desc">Review AST-detected security policy breaches and blocked system calls.</p>
      </div>
    </div>

    <div v-if="flaggedSubmissions.length > 0" class="cards-list">
      <PixelCard
        v-for="sub in flaggedSubmissions"
        :key="sub.id"
        class="item-card flagged-card"
      >
        <PixelCardContent>
          <div class="card-inner">
            <div class="card-meta">
              <PixelBadge color="danger" text="SECURITY VIOLATION" />
              <span class="meta-tag"><PixelIcon name="user" :size="12" /> Assignment #{{ sub.daily_assignment_id }}</span>
              <span class="meta-tag"><PixelIcon name="calendar" :size="12" /> {{ new Date(sub.submitted_at || sub.created_at || Date.now()).toLocaleString() }}</span>
            </div>

            <div class="code-snippet-box">
              <pre class="snippet-code">{{ sub.source_code }}</pre>
            </div>

            <PixelCardActions class="review-actions">
              <PixelButton
                color="danger"
                size="small"
                icon="trash"
                @click="emit('resolve', { submissionId: sub.id, resolution: 'action' })"
              >
                Strike Student
              </PixelButton>
              <PixelButton
                size="small"
                color="success"
                icon="check"
                @click="emit('resolve', { submissionId: sub.id, resolution: 'dismiss' })"
              >
                Dismiss Flag
              </PixelButton>
            </PixelCardActions>
          </div>
        </PixelCardContent>
      </PixelCard>
    </div>

    <PixelCard v-else class="empty-pool-card">
      <PixelCardContent class="empty-content">
        <PixelSprite name="shield" :size="48" class="empty-pool-icon" />
        <h3 class="empty-title">No Flagged Submissions</h3>
        <p>All student code submissions conform to AST sandbox policies.</p>
      </PixelCardContent>
    </PixelCard>
  </div>
</template>

<style scoped>
.pool-container {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.pool-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  margin: 0;
  font-family: var(--font-pixel);
  font-size: 1.25rem;
  color: var(--pixel-text);
}

.section-desc {
  margin: 0.25rem 0 0;
  font-size: 0.85rem;
  color: var(--pixel-text-muted);
}

.cards-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.flagged-card {
  border-left: 4px solid var(--pixel-btn-danger-bg);
}

.card-inner {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  flex-wrap: wrap;
}

.meta-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8rem;
  color: var(--pixel-text-dim);
}

.code-snippet-box {
  background-color: var(--pixel-bg-alt);
  border: 2px solid var(--pixel-border);
  border-radius: 3px;
  padding: 8px 12px;
}

.snippet-code {
  font-family: var(--font-mono);
  font-size: 12px;
  margin: 0;
  white-space: pre-wrap;
  color: var(--pixel-text);
}

.review-actions {
  padding: 0;
  background: transparent;
  border-top: none;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.empty-pool-card {
  text-align: center;
}

.empty-content {
  padding: 3rem 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  color: var(--pixel-text-dim);
}

.empty-title {
  font-family: var(--font-pixel);
  font-size: 1.2rem;
  color: var(--pixel-text);
  margin: 0;
}
</style>
