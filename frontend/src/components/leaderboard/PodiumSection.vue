<script setup lang="ts">
import { computed } from 'vue'
import type { LeaderboardEntry } from '@/types'
import PixelCard from '@/components/pixel/PixelCard.vue'
import PixelCardContent from '@/components/pixel/PixelCardContent.vue'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'

const props = defineProps<{
  entries: LeaderboardEntry[]
}>()

const champion = computed<LeaderboardEntry | null>(() => props.entries[0] || null)
const runnerUp = computed<LeaderboardEntry | null>(() => props.entries[1] || null)
const thirdPlace = computed<LeaderboardEntry | null>(() => props.entries[2] || null)
</script>

<template>
  <section v-if="champion" class="podium-section">
    <!-- 2nd Place (Silver) -->
    <PixelCard v-if="runnerUp" class="podium-card silver-card">
      <PixelCardContent class="podium-content">
        <div class="medal-icon silver-medal">
          <PixelSprite name="star_silver" :size="36" />
        </div>
        <span class="podium-rank">Rank #2</span>
        <h3 class="podium-name">{{ runnerUp.name }}</h3>
        <span class="podium-roll">{{ runnerUp.roll_number || 'Student' }}</span>
        <div class="podium-stats">
          <PixelBadge :text="`${runnerUp.total_points} XP`" color="primary" />
          <div class="streak-pill">
            <PixelSprite name="flame" :size="14" />
            <span>{{ runnerUp.current_streak }}</span>
          </div>
        </div>
      </PixelCardContent>
    </PixelCard>

    <!-- 1st Place (Gold Champion / Center) -->
    <PixelCard class="podium-card gold-card">
      <PixelCardContent class="podium-content">
        <div class="medal-icon gold-medal">
          <PixelSprite name="star_gold" :size="48" />
        </div>
        <span class="podium-rank gold-rank">Champion</span>
        <h3 class="podium-name gold-name">{{ champion.name }}</h3>
        <span class="podium-roll">{{ champion.roll_number || 'Student' }}</span>
        <div class="podium-stats">
          <PixelBadge :text="`${champion.total_points} XP`" color="primary" />
          <div class="streak-pill">
            <PixelSprite name="flame" :size="14" />
            <span>{{ champion.current_streak }}</span>
          </div>
        </div>
      </PixelCardContent>
    </PixelCard>

    <!-- 3rd Place (Bronze) -->
    <PixelCard v-if="thirdPlace" class="podium-card bronze-card">
      <PixelCardContent class="podium-content">
        <div class="medal-icon bronze-medal">
          <PixelSprite name="star_bronze" :size="32" />
        </div>
        <span class="podium-rank">Rank #3</span>
        <h3 class="podium-name">{{ thirdPlace.name }}</h3>
        <span class="podium-roll">{{ thirdPlace.roll_number || 'Student' }}</span>
        <div class="podium-stats">
          <PixelBadge :text="`${thirdPlace.total_points} XP`" color="primary" />
          <div class="streak-pill">
            <PixelSprite name="flame" :size="14" />
            <span>{{ thirdPlace.current_streak }}</span>
          </div>
        </div>
      </PixelCardContent>
    </PixelCard>
  </section>
</template>

<style scoped>
.podium-section {
  display: grid;
  grid-template-columns: 1fr 1.15fr 1fr;
  gap: 1.25rem;
  align-items: end;
  margin-bottom: 2rem;
}

@media (max-width: 768px) {
  .podium-section {
    grid-template-columns: 1fr;
  }
}

.podium-content {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1.5rem 1rem;
}

.medal-icon {
  margin-bottom: 0.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.gold-card {
  border-color: #f59e0b;
  box-shadow: 0 6px 0 0 #b45309;
  background-color: #2a2016;
}

.silver-card {
  border-color: #94a3b8;
  box-shadow: 0 5px 0 0 #475569;
  background-color: #1e222d;
}

.bronze-card {
  border-color: #b45309;
  box-shadow: 0 5px 0 0 #78350f;
  background-color: #281a14;
}

.podium-rank {
  font-family: var(--font-pixel);
  font-size: 11px;
  text-transform: uppercase;
  color: var(--pixel-text-dim);
  letter-spacing: 0.05em;
}

.gold-rank {
  color: #fbbf24;
}

.podium-name {
  font-family: var(--font-pixel);
  font-size: 1.25rem;
  margin: 0;
  color: var(--pixel-text);
  line-height: 1.2;
}

.gold-name {
  font-size: 1.4rem;
  color: #fef08a;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
}

.podium-roll {
  font-size: 0.8rem;
  color: var(--pixel-text-muted);
}

.podium-stats {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
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
</style>
