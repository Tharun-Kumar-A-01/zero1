<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { AVAILABLE_FACES, getAvatarUrl, type FaceItem } from '@/utils/avatar'
import PixelModal from '@/components/pixel/PixelModal.vue'
import PixelButton from '@/components/pixel/PixelButton.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'selected', avatarId: string | null): void
}>()

const authStore = useAuthStore()
const selectedAvatar = ref<string | null>(authStore.user?.avatar || null)
const isSaving = ref<boolean>(false)
const searchQuery = ref<string>('')

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      selectedAvatar.value = authStore.user?.avatar || null
      searchQuery.value = ''
    }
  }
)

const filteredFaces = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return AVAILABLE_FACES
  return AVAILABLE_FACES.filter((f) => f.name.toLowerCase().includes(q) || f.id.includes(q))
})

function selectFace(face: FaceItem): void {
  selectedAvatar.value = face.id
}

function clearAvatar(): void {
  selectedAvatar.value = null
}

async function handleSave(): Promise<void> {
  isSaving.value = true
  try {
    const ok = await authStore.updateAvatar(selectedAvatar.value)
    if (ok) {
      emit('selected', selectedAvatar.value)
      emit('update:modelValue', false)
    }
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <PixelModal
    :model-value="modelValue"
    hide-default-actions
    title="Choose Profile Avatar"
    max-width="540px"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="avatar-picker">
      <!-- CURRENT PREVIEW HEADER -->
      <div class="picker-preview-bar">
        <div class="current-avatar-preview">
          <div class="preview-box">
            <img
              v-if="selectedAvatar && getAvatarUrl(selectedAvatar)"
              :src="getAvatarUrl(selectedAvatar)!"
              :alt="selectedAvatar"
              class="preview-img"
            />
            <div v-else class="preview-placeholder">
              {{ authStore.user?.name ? authStore.user.name.charAt(0).toUpperCase() : '?' }}
            </div>
          </div>
          <div class="preview-info">
            <div class="preview-label">Selected Avatar</div>
            <div class="preview-name">
              {{ selectedAvatar ? selectedAvatar.replace(/_/g, ' ') : 'Default Initials' }}
            </div>
          </div>
        </div>

        <div class="preview-actions">
          <PixelButton
            v-if="selectedAvatar"
            color="secondary"
            size="small"
            @click="clearAvatar"
          >
            Clear
          </PixelButton>
        </div>
      </div>

      <!-- SEARCH / FILTER BAR -->
      <div class="search-row">
        <input
          v-model="searchQuery"
          type="text"
          class="picker-search-input"
          placeholder="Filter avatars (e.g. spiderman, emoji)..."
        />
      </div>

      <!-- AVATAR GRID -->
      <div class="avatar-grid-container">
        <div class="avatar-grid">
          <button
            v-for="face in filteredFaces"
            :key="face.id"
            type="button"
            :class="['face-tile', { 'face-tile--active': selectedAvatar === face.id }]"
            :title="face.name"
            @click="selectFace(face)"
          >
            <div class="tile-icon-wrap">
              <img :src="face.url" :alt="face.name" class="face-img" />
            </div>
            <span class="face-title">{{ face.name }}</span>
            <div v-if="selectedAvatar === face.id" class="tile-check">
              <PixelIcon name="check" :size="10" />
            </div>
          </button>
        </div>
      </div>

      <!-- FOOTER ACTIONS -->
      <div class="picker-modal-actions">
        <PixelButton
          color="secondary"
          @click="emit('update:modelValue', false)"
        >
          Cancel
        </PixelButton>

        <PixelButton
          color="primary"
          :loading="isSaving"
          icon="check"
          @click="handleSave"
        >
          Equip Avatar
        </PixelButton>
      </div>
    </div>
  </PixelModal>
</template>

<style scoped>
.avatar-picker {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.picker-preview-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: var(--pixel-surface-raised);
  border: 2px solid var(--pixel-border);
  padding: 0.75rem 1rem;
}

.current-avatar-preview {
  display: flex;
  align-items: center;
  gap: 12px;
}

.preview-box {
  width: 44px;
  height: 44px;
  background-color: var(--pixel-bg);
  border: 2px solid var(--pixel-border-bright);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.preview-img {
  width: 32px;
  height: 32px;
  image-rendering: pixelated;
  object-fit: contain;
}

.preview-placeholder {
  font-family: var(--font-pixel);
  font-size: 1.2rem;
  color: var(--pixel-text);
}

.preview-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.preview-label {
  font-size: 0.75rem;
  color: var(--pixel-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.preview-name {
  font-family: var(--font-pixel);
  font-size: 0.95rem;
  color: var(--pixel-text);
  text-transform: capitalize;
}

.search-row {
  display: flex;
}

.picker-search-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  background-color: var(--pixel-bg);
  border: 2px solid var(--pixel-border);
  color: var(--pixel-text);
  font-family: inherit;
  font-size: 0.85rem;
  outline: none;
}

.picker-search-input:focus {
  border-color: var(--pixel-btn-primary-hover);
}

.avatar-grid-container {
  max-height: 280px;
  overflow-y: auto;
  border: 2px solid var(--pixel-border);
  background-color: var(--pixel-bg-alt);
  padding: 0.75rem;
}

.avatar-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
  gap: 0.5rem;
}

.face-tile {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 4px;
  background-color: var(--pixel-surface);
  border: 2px solid var(--pixel-border);
  cursor: pointer;
  transition: all 0.15s ease;
}

.face-tile:hover {
  background-color: var(--pixel-surface-raised);
  border-color: var(--pixel-border-bright);
}

.face-tile--active {
  background-color: var(--pixel-surface-raised);
  border-color: var(--pixel-btn-primary-hover);
  box-shadow: 0 0 0 1px var(--pixel-btn-primary-hover);
}

.tile-icon-wrap {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.face-img {
  width: 24px;
  height: 24px;
  image-rendering: pixelated;
  object-fit: contain;
}

.face-title {
  font-family: var(--font-pixel);
  font-size: 0.65rem;
  color: var(--pixel-text-muted);
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80px;
}

.face-tile--active .face-title {
  color: var(--pixel-text);
}

.tile-check {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 14px;
  height: 14px;
  background-color: var(--pixel-btn-success-bg);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.picker-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding-top: 0.5rem;
  border-top: 2px solid var(--pixel-border);
}
</style>
