<script setup lang="ts">
import type { LeaderboardEntry } from '@/types'
import PixelCard from '@/components/pixel/PixelCard.vue'
import PixelCardContent from '@/components/pixel/PixelCardContent.vue'
import PixelDataTable from '@/components/pixel/PixelDataTable.vue'
import PixelAvatar from '@/components/pixel/PixelAvatar.vue'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'

defineProps<{
  entries: LeaderboardEntry[]
  currentUserId?: number
}>()

const columns = [
  { key: 'rank', label: 'Rank', width: '80px' },
  { key: 'name', label: 'Adventurer' },
  { key: 'roll_number', label: 'Roll Number' },
  { key: 'year_batch', label: 'Cohort' },
  { key: 'current_streak', label: 'Streak' },
  { key: 'total_points', label: 'Score' },
]
</script>

<template>
  <div class="rankings-container">
    <PixelCard v-if="entries.length > 0">
      <PixelCardContent>
        <PixelDataTable
          :items="entries"
          :columns="columns"
          striped
          hoverable
        >
          <template #cell(rank)="{ value }">
            <div class="rank-cell">
              <PixelSprite v-if="Number(value) === 1" name="crown" :size="20" />
              <PixelSprite v-else-if="Number(value) === 2" name="silver" :size="20" />
              <PixelSprite v-else-if="Number(value) === 3" name="bronze" :size="20" />
              <span v-else class="rank-number">#{{ value }}</span>
            </div>
          </template>

          <template #cell(name)="{ rowData }">
            <div class="student-cell">
              <PixelAvatar size="small" color="primary">
                {{ (rowData as LeaderboardEntry).name.split(' ').map((n) => n[0]).join('').substring(0, 2).toUpperCase() }}
              </PixelAvatar>
              <div class="student-name-group">
                <span class="student-fullname">{{ (rowData as LeaderboardEntry).name }}</span>
                <PixelBadge
                  v-if="(rowData as LeaderboardEntry).student_id === currentUserId"
                  text="YOU"
                  color="primary"
                />
              </div>
            </div>
          </template>

          <template #cell(roll_number)="{ value }">
            <span class="font-mono-val">{{ value || '—' }}</span>
          </template>

          <template #cell(year_batch)="{ value }">
            <span>{{ value ? `Batch ${value}` : '—' }}</span>
          </template>

          <template #cell(current_streak)="{ value }">
            <div class="streak-pill">
              <PixelSprite name="flame" :size="14" />
              <span>{{ value }}d</span>
            </div>
          </template>

          <template #cell(total_points)="{ value }">
            <span class="points-val">{{ value }} XP</span>
          </template>
        </PixelDataTable>
      </PixelCardContent>
    </PixelCard>

    <PixelCard v-else class="empty-leaderboard-card">
      <PixelCardContent class="empty-state">
        <PixelSprite name="crown" :size="48" class="empty-icon" />
        <h3 class="empty-title">No rankings recorded yet</h3>
        <p>Be the first student in this batch to solve today's challenge and top the leaderboard!</p>
      </PixelCardContent>
    </PixelCard>
  </div>
</template>

<style scoped>
.rankings-container {
  width: 100%;
}

.rank-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
}

.rank-number {
  font-family: var(--font-pixel);
  font-size: 12px;
  color: var(--pixel-text-dim);
}

.student-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.student-name-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.student-fullname {
  font-family: var(--font-body);
  font-weight: 600;
  color: var(--pixel-text);
}

.font-mono-val {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--pixel-text-muted);
}

.streak-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background-color: #2b1704;
  border: 1px solid #7e4507;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: var(--font-pixel);
  font-size: 11px;
  color: #fbbf24;
}

.points-val {
  font-family: var(--font-pixel);
  font-size: 12px;
  color: #fbbf24;
}

.empty-state {
  text-align: center;
  padding: 3rem 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  color: var(--pixel-text-muted);
}

.empty-title {
  font-family: var(--font-pixel);
  font-size: 1.25rem;
  color: var(--pixel-text);
  margin: 0;
}
</style>
