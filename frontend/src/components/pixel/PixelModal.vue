<script setup lang="ts">
import { watch, onMounted, onUnmounted } from 'vue'
import PixelButton from './PixelButton.vue'
import PixelIcon from './PixelIcon.vue'

interface Props {
  modelValue: boolean
  title?: string
  okText?: string
  okColor?: 'primary' | 'secondary' | 'danger' | 'warning' | 'info' | 'success'
  cancelText?: string
  hideDefaultActions?: boolean
  loading?: boolean
  maxWidth?: string
  size?: 'small' | 'medium' | 'large'
}

const props = withDefaults(defineProps<Props>(), {
  okText: 'OK',
  okColor: 'primary',
  cancelText: 'Cancel',
  hideDefaultActions: false,
  loading: false,
  maxWidth: '560px',
  size: 'medium',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'ok'): void
  (e: 'cancel'): void
}>()

const handleClose = () => {
  emit('update:modelValue', false)
  emit('cancel')
}

const handleOk = () => {
  emit('ok')
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.modelValue) {
    handleClose()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  },
)
</script>

<template>
  <Teleport to="body">
    <Transition name="pixel-modal-fade">
      <div v-if="modelValue" class="pixel-modal-backdrop" @click.self="handleClose">
        <div
          :class="['pixel-modal-container', `pixel-modal--${size}`]"
          :style="{ maxWidth: maxWidth }"
          role="dialog"
          aria-modal="true"
        >
          <!-- Header -->
          <div class="pixel-modal-header">
            <h3 class="pixel-modal-title">
              <slot name="header">{{ title }}</slot>
            </h3>
            <button
              type="button"
              class="pixel-modal-close-btn"
              aria-label="Close dialog"
              @click="handleClose"
            >
              <PixelIcon name="cross" :size="14" />
            </button>
          </div>

          <!-- Body -->
          <div class="pixel-modal-body">
            <slot />
          </div>

          <!-- Footer -->
          <div v-if="!hideDefaultActions || $slots.footer" class="pixel-modal-footer">
            <slot name="footer">
              <PixelButton
                color="secondary"
                @click="handleClose"
              >
                {{ cancelText }}
              </PixelButton>
              <PixelButton
                :color="okColor"
                :loading="loading"
                @click="handleOk"
              >
                {{ okText }}
              </PixelButton>
            </slot>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.pixel-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background-color: rgba(12, 10, 18, 0.78);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.pixel-modal-container {
  --pixel-tab-active-bg: var(--pixel-surface);
  width: 100%;
  background-color: var(--pixel-surface);
  border: 3px solid var(--pixel-border);
  box-shadow: 0 6px 0 0 var(--pixel-border-dark), 0 16px 32px rgba(0, 0, 0, 0.6);
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  max-height: 90vh;
  overflow: hidden;
  animation: modalPop 0.12s ease-out;
}

.pixel-modal-header {
  padding: 12px 16px;
  background-color: var(--pixel-surface-alt);
  border-bottom: 2px solid var(--pixel-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.pixel-modal-title {
  margin: 0;
  font-family: var(--font-pixel);
  font-size: 14px;
  color: var(--pixel-text);
  letter-spacing: -0.01em;
}

.pixel-modal-close-btn {
  background: none;
  border: none;
  color: var(--pixel-text-muted);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.1s;
}

.pixel-modal-close-btn:hover {
  color: var(--pixel-text);
}

.pixel-modal-body {
  padding: 16px;
  overflow-y: auto;
  font-family: var(--font-body);
  color: var(--pixel-text);
  flex: 1 1 auto;
}

.pixel-modal-footer {
  padding: 12px 16px;
  background-color: var(--pixel-surface-alt);
  border-top: 2px solid var(--pixel-border);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

@keyframes modalPop {
  0% {
    transform: scale(0.95);
    opacity: 0;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.pixel-modal-fade-enter-active,
.pixel-modal-fade-leave-active {
  transition: opacity 0.15s ease;
}

.pixel-modal-fade-enter-from,
.pixel-modal-fade-leave-to {
  opacity: 0;
}
</style>
