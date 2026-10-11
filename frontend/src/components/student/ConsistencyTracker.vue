<script setup lang="ts">
import { computed } from 'vue'
import type { ProgressData } from '@/types'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelCard from '@/components/pixel/PixelCard.vue'
import PixelCardTitle from '@/components/pixel/PixelCardTitle.vue'
import PixelCardContent from '@/components/pixel/PixelCardContent.vue'
import PixelAvatar from '@/components/pixel/PixelAvatar.vue'
import PixelProgressBar from '@/components/pixel/PixelProgressBar.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'
import PixelFlame from '@/components/pixel/PixelFlame.vue'

const props = defineProps<{
  progress: ProgressData | null
  isTodaySolved: boolean
}>()

const currentTier = computed<string>(() => {
  const pts: number = props.progress?.total_points ?? 0
  if (pts >= 1000) return 'Master Coder'
  if (pts >= 500) return 'Gold Apprentice'
  if (pts >= 200) return 'Silver Solver'
  return 'Bronze Explorer'
})

const tierProgressPercent = computed<number>(() => {
  const pts: number = props.progress?.total_points ?? 0
  if (pts >= 1000) return 100
  if (pts >= 500) return Math.min(100, Math.round(((pts - 500) / 500) * 100))
  if (pts >= 200) return Math.min(100, Math.round(((pts - 200) / 300) * 100))
  return Math.min(100, Math.round((pts / 200) * 100))
})

const daysOfWeek = computed<Array<{ day: string; dateStr: string; isPast: boolean; isToday: boolean; isCompleted: boolean }>>(() => {
  const days: Array<{ day: string; dateStr: string; isPast: boolean; isToday: boolean; isCompleted: boolean }> = []
  const now = new Date()
  const dayNames: string[] = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  const currentDayIndex: number = now.getDay()
  const streak: number = props.progress?.current_streak ?? 0

  function workingDaysAgo(d: Date): number {
    let count = 0
    const cursor = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const target = new Date(d.getFullYear(), d.getMonth(), d.getDate())
    while (cursor > target) {
      cursor.setDate(cursor.getDate() - 1)
      if (cursor.getDay() !== 0) count++
    }
    return count
  }

  const mondayOffset = currentDayIndex === 0 ? -6 : 1 - currentDayIndex
  for (let i = 0; i < 7; i++) {
    const d = new Date(now)
    d.setDate(now.getDate() + mondayOffset + i)
    const isToday = d.toDateString() === now.toDateString()
    const isPast = d < now && !isToday

    let isCompleted = false
    if (isToday) {
      isCompleted = props.isTodaySolved
    } else if (isPast && d.getDay() !== 0) {
      const daysAgo = workingDaysAgo(d)
      const threshold = props.isTodaySolved ? streak - 1 : streak
      isCompleted = streak > 0 && daysAgo <= threshold
    }
    days.push({
      day: dayNames[d.getDay()] || 'Sun',
      dateStr: d.getDate().toString(),
      isPast,
      isToday,
      isCompleted,
    })
  }
  return days
})
</script>

<template>
  <PixelCard class="tracker-card">
    <PixelCardTitle class="tracker-header">
      <PixelFlame :active="(progress?.current_streak ?? 0) > 0" :ignite="isTodaySolved" :size="20" />
      <span class="tracker-title">Consistency Tracker</span>
    </PixelCardTitle>

    <PixelCardContent>
      <div class="streak-story">
        <div class="streak-headline">
          <!-- Animated Pixel Flame with Ember Burst when streak is solved/active -->
          <div class="streak-flame-wrapper">
            <PixelFlame
              :active="(progress?.current_streak ?? 0) > 0"
              :ignite="isTodaySolved"
              :size="48"
            />
          </div>
          <span class="streak-count">{{ progress?.current_streak ?? 0 }}</span>
          <div class="streak-text-group">
            <span class="streak-main-label">Day Active Streak</span>
            <span class="streak-best-label">Personal best: {{ progress?.longest_streak ?? 0 }} days</span>
          </div>
        </div>

        <!-- 7-Day Visual Chain -->
        <div class="weekly-chain-card">
          <div class="weekly-chain">
            <div
              v-for="(dayItem, idx) in daysOfWeek"
              :key="idx"
              class="day-node"
            >
              <span class="day-name">{{ dayItem.day }}</span>
              <PixelAvatar
                size="small"
                :color="dayItem.isCompleted ? 'success' : dayItem.isToday ? 'primary' : 'secondary'"
              >
                <PixelIcon v-if="dayItem.isCompleted" name="check" :size="12" />
                <span v-else class="day-num">{{ dayItem.dateStr }}</span>
              </PixelAvatar>
            </div>
          </div>
        </div>

        <!-- Tier Level Progression -->
        <div class="tier-progress-section">
          <div class="tier-labels">
            <span class="tier-name">{{ currentTier }}</span>
            <PixelBadge :text="`${progress?.total_points ?? 0} XP`" color="primary" />
          </div>
          <PixelProgressBar :model-value="tierProgressPercent" color="warning" class="tier-progress-bar" />
          <span class="tier-subtext">Earn points daily by solving assigned questions</span>
        </div>
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
  color: var(--pixel-text);
}

.streak-story {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.streak-headline {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.streak-flame-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.streak-count {
  font-family: var(--font-pixel);
  font-size: 2.75rem;
  color: #fbbf24;
  line-height: 1;
}

.streak-text-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.streak-main-label {
  font-family: var(--font-pixel);
  font-size: 1.1rem;
  color: var(--pixel-text);
}

.streak-best-label {
  font-size: 0.8rem;
  color: var(--pixel-text-dim);
}

.weekly-chain-card {
  background-color: var(--pixel-bg-alt);
  border: 2px solid var(--pixel-border);
  box-shadow: inset 0 2px 0 0 rgba(0, 0, 0, 0.4);
  border-radius: 4px;
  padding: 12px;
}

.weekly-chain {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.day-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.day-name {
  font-family: var(--font-pixel);
  font-size: 11px;
  color: var(--pixel-text-muted);
}

.day-num {
  font-family: var(--font-pixel);
  font-size: 11px;
}

.tier-progress-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tier-labels {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tier-name {
  font-family: var(--font-pixel);
  font-size: 13px;
  color: var(--pixel-text);
}

.tier-progress-bar {
  margin-bottom: 2px;
}

.tier-subtext {
  font-size: 0.8rem;
  color: var(--pixel-text-dim);
}
</style>
