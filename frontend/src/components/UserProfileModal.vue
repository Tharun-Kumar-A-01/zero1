<script setup lang="ts">
import { computed } from 'vue'
import PixelModal from '@/components/pixel/PixelModal.vue'
import PixelAvatar from '@/components/pixel/PixelAvatar.vue'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelButton from '@/components/pixel/PixelButton.vue'
import PixelCard from '@/components/pixel/PixelCard.vue'
import PixelCardContent from '@/components/pixel/PixelCardContent.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'
import PixelFlame from '@/components/pixel/PixelFlame.vue'

const props = defineProps<{
  modelValue: boolean
  user: {
    id?: number
    name: string
    email: string
    role: string
    current_streak?: number
    total_points?: number
    roll_number?: string | null
    year_batch?: string | null
    section?: string | null
  } | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
}>()

const streakCount = computed<number>(() => props.user?.current_streak ?? 0)

// Generate the 7 days of the current week (Sat, Sun, Mon, Tue, Wed, Thu, Fri)
const weekDays = computed(() => {
  const names = ['Sat', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri']
  const todayIndex = new Date().getDay()
  const mapToIdx = (d: number) => (d === 6 ? 0 : d + 1)
  const currentIdx = mapToIdx(todayIndex)

  return names.map((name, i) => {
    const isWeekend = i === 0 || i === 1
    const isSolved = streakCount.value > 0 && i <= currentIdx && !isWeekend
    const isCurrentDay = i === currentIdx
    return {
      name,
      isWeekend,
      isSolved,
      isCurrentDay,
    }
  })
})
</script>

<template>
  <PixelModal
    :model-value="modelValue"
    hide-default-actions
    title="Adventurer Profile"
    max-width="500px"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div v-if="user" class="profile-container">
      <!-- User Header Information -->
      <div class="user-header-card">
        <PixelAvatar size="large" color="primary" class="profile-avatar">
          {{ user.name.charAt(0).toUpperCase() }}
        </PixelAvatar>
        <div class="profile-meta">
          <h3 class="profile-name">{{ user.name }}</h3>
          <span class="profile-email">{{ user.email }}</span>
          <div class="profile-badges">
            <PixelBadge
              :text="user.role === 'admin' ? 'ADMIN' : user.role.toUpperCase()"
              :color="user.role === 'admin' ? 'danger' : user.role === 'mentor' ? 'warning' : 'primary'"
            />
            <PixelBadge
              v-if="user.roll_number"
              :text="user.roll_number"
              color="secondary"
            />
            <PixelBadge
              v-if="user.year_batch"
              :text="`Batch ${user.year_batch}`"
              color="secondary"
            />
            <PixelBadge
              v-if="user.total_points !== undefined"
              :text="`${user.total_points ?? 0} XP`"
              color="primary"
            />
          </div>
        </div>
      </div>

      <!-- Streak Showcase Box -->
      <PixelCard class="streak-box-card">
        <PixelCardContent>
          <div class="streak-top-row">
            <span class="streak-number">{{ streakCount }}</span>
            <div class="streak-flame-group">
              <PixelFlame :active="streakCount > 0" :size="36" />
              <span class="streak-label">Current streak</span>
            </div>
          </div>

          <div class="pixel-divider" />

          <!-- 7 Days Circles Row -->
          <div class="days-row">
            <div
              v-for="(day, idx) in weekDays"
              :key="idx"
              class="day-col"
            >
              <div
                class="day-circle"
                :class="{
                  'is-weekend': day.isWeekend,
                  'is-solved': day.isSolved,
                  'is-today': day.isCurrentDay,
                }"
              >
                <PixelIcon
                  v-if="day.isSolved"
                  name="check"
                  :size="12"
                  color="#fff"
                />
              </div>
              <span class="day-name" :class="{ 'highlight': day.isCurrentDay }">
                {{ day.name }}
              </span>
            </div>
          </div>
        </PixelCardContent>
      </PixelCard>

      <div class="profile-actions">
        <PixelButton color="secondary" size="small" @click="emit('update:modelValue', false)">
          Close
        </PixelButton>
      </div>
    </div>
  </PixelModal>
</template>

<style scoped>
.profile-container {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.user-header-card {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.profile-avatar {
  font-size: 1.5rem;
  font-weight: 700;
  width: 54px;
  height: 54px;
  flex-shrink: 0;
}

.profile-meta {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  overflow: hidden;
}

.profile-name {
  font-family: var(--font-pixel);
  font-size: 1.25rem;
  font-weight: normal;
  margin: 0;
  color: var(--pixel-text);
}

.profile-email {
  font-size: 0.85rem;
  color: var(--pixel-text-muted);
}

.profile-badges {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
  margin-top: 0.35rem;
}

.streak-top-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.streak-number {
  font-family: var(--font-pixel);
  font-size: 2.75rem;
  font-weight: normal;
  color: #fbbf24;
  line-height: 1;
}

.streak-flame-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.streak-label {
  font-family: var(--font-pixel);
  font-size: 1rem;
  color: var(--pixel-text);
}

.pixel-divider {
  height: 2px;
  background-color: var(--pixel-border);
  margin: 0.85rem 0;
}

.days-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem;
}

.day-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
}

.day-circle {
  width: 32px;
  height: 32px;
  border-radius: 3px;
  border: 2px solid var(--pixel-border);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--pixel-bg-alt);
  box-shadow: 0 2px 0 0 rgba(0, 0, 0, 0.3);
  transition: all 0.15s ease;
}

.day-circle.is-solved {
  background: var(--pixel-btn-success-bg);
  border-color: var(--pixel-btn-success-border);
  box-shadow: 0 2px 0 0 var(--pixel-btn-success-shade);
}

.day-circle.is-today:not(.is-solved) {
  border-color: var(--pixel-btn-primary-bg);
}

.day-circle.is-weekend {
  opacity: 0.4;
}

.day-name {
  font-family: var(--font-pixel);
  font-size: 0.7rem;
  color: var(--pixel-text-dim);
}

.day-name.highlight {
  color: #fbbf24;
}

.profile-actions {
  display: flex;
  justify-content: flex-end;
}
</style>
