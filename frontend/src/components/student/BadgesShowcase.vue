<script setup lang="ts">
import type { StudentRewardBadge } from '@/types'
import PixelCard from '@/components/pixel/PixelCard.vue'
import PixelCardTitle from '@/components/pixel/PixelCardTitle.vue'
import PixelCardContent from '@/components/pixel/PixelCardContent.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'

defineProps<{
  badges: StudentRewardBadge[]
}>()

const gemTypes = ['gem_ruby', 'gem_emerald', 'gem_sapphire', 'gem_amber', 'gem_diamond']

function getBadgeGem(badge: StudentRewardBadge, index: number): string {
  const name = (badge.reward_name || '').toLowerCase()
  if (name.includes('ruby') || name.includes('red') || name.includes('flame') || name.includes('master')) return 'gem_ruby'
  if (name.includes('emerald') || name.includes('green') || name.includes('apprentice')) return 'gem_emerald'
  if (name.includes('sapphire') || name.includes('blue') || name.includes('silver') || name.includes('expert')) return 'gem_sapphire'
  if (name.includes('amber') || name.includes('gold') || name.includes('topaz') || name.includes('streak')) return 'gem_amber'
  if (name.includes('diamond') || name.includes('pearl') || name.includes('champion')) return 'gem_diamond'
  return gemTypes[index % gemTypes.length] ?? 'gem_ruby'
}
</script>

<template>
  <PixelCard class="badges-card">
    <PixelCardTitle class="tracker-header">
      <PixelSprite name="shield" :size="18" />
      <span class="tracker-title">Earned Milestones</span>
    </PixelCardTitle>

    <PixelCardContent>
      <div v-if="badges && badges.length > 0" class="pixel-list">
        <div
          v-for="(badge, idx) in badges"
          :key="badge.id"
          class="badge-item"
        >
          <div class="badge-avatar-wrap">
            <PixelSprite :name="getBadgeGem(badge, idx)" :size="20" />
          </div>

          <div class="badge-meta">
            <span class="badge-title">
              {{ badge.reward_name }}
            </span>
            <span class="badge-caption">
              Earned {{ new Date(badge.awarded_at).toLocaleDateString() }}
            </span>
          </div>
        </div>
      </div>

      <div v-else class="no-badges-msg">
        <PixelSprite name="chest" :size="28" />
        <p>Complete challenges to unlock your first streak milestone badge!</p>
      </div>
    </PixelCardContent>
  </PixelCard>
</template>

<style scoped>
.tracker-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.tracker-title {
  font-family: var(--font-pixel);
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--pixel-text);
}

.pixel-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.badge-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background-color: var(--pixel-surface-alt);
  border: 1px solid var(--pixel-border);
  border-radius: 3px;
}

.badge-avatar-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
}

.badge-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.badge-title {
  font-family: var(--font-body);
  font-weight: 600;
  font-size: 13px;
  color: var(--pixel-text);
}

.badge-caption {
  font-size: 11px;
  color: var(--pixel-text-dim);
}

.no-badges-msg {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 8px;
  text-align: center;
  color: var(--pixel-text-muted);
  font-size: 12px;
}
</style>
