<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

interface Props {
  rank?: number
  aura?: 'gold' | 'silver' | 'bronze'
}

const props = defineProps<Props>()

const effectiveAura = computed<'gold' | 'silver' | 'bronze' | null>(() => {
  if (props.aura) return props.aura
  if (props.rank === 1) return 'gold'
  if (props.rank === 2) return 'silver'
  if (props.rank === 3) return 'bronze'
  return null
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)
let animId: number | null = null

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  alpha: number
  color: string
  life: number
  maxLife: number
}

let particles: Particle[] = []

const AURA_COLORS = {
  gold: ['#fbbf24', '#f59e0b', '#fef08a', '#ffffff', '#d97706'],
  silver: ['#f1f5f9', '#e2e8f0', '#cbd5e1', '#94a3b8', '#ffffff'],
  bronze: ['#f97316', '#d97706', '#b45309', '#78350f', '#fed7aa'],
}

function spawnParticle() {
  if (!canvasRef.value || !effectiveAura.value) return
  const w = canvasRef.value.width
  const h = canvasRef.value.height
  const palette = AURA_COLORS[effectiveAura.value]

  // Spawn around outer border perimeter
  const side = Math.floor(Math.random() * 4)
  let x = 0
  let y = 0
  let vx = 0
  let vy = 0

  if (side === 0) { // Top
    x = Math.random() * w
    y = 4
    vy = -(Math.random() * 0.8 + 0.3)
    vx = (Math.random() - 0.5) * 0.6
  } else if (side === 1) { // Bottom
    x = Math.random() * w
    y = h - 4
    vy = Math.random() * 0.8 + 0.3
    vx = (Math.random() - 0.5) * 0.6
  } else if (side === 2) { // Left
    x = 4
    y = Math.random() * h
    vx = -(Math.random() * 0.8 + 0.3)
    vy = (Math.random() - 0.5) * 0.6
  } else { // Right
    x = w - 4
    y = Math.random() * h
    vx = Math.random() * 0.8 + 0.3
    vy = (Math.random() - 0.5) * 0.6
  }

  const p: Particle = {
    x,
    y,
    vx,
    vy,
    size: Math.random() > 0.5 ? 4 : 3,
    alpha: 1,
    color: palette[Math.floor(Math.random() * palette.length)] ?? '#f59e0b',
    life: 0,
    maxLife: 30 + Math.random() * 30,
  }
  particles.push(p)
}

function resizeCanvas() {
  if (!containerRef.value || !canvasRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  canvasRef.value.width = rect.width + 32
  canvasRef.value.height = rect.height + 32
}

function animate() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, canvas.width, canvas.height)

  if (effectiveAura.value && Math.random() < 0.6) {
    spawnParticle()
  }

  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i]
    if (!p) continue
    p.x += p.vx
    p.y += p.vy
    p.life++
    p.alpha = 1 - p.life / p.maxLife

    if (p.alpha <= 0 || p.life >= p.maxLife) {
      particles.splice(i, 1)
      continue
    }

    ctx.fillStyle = p.color
    ctx.globalAlpha = Math.max(0, p.alpha)
    const px = Math.round(p.x)
    const py = Math.round(p.y)
    ctx.fillRect(px, py, p.size, p.size)
  }

  ctx.globalAlpha = 1
  animId = requestAnimationFrame(animate)
}

onMounted(() => {
  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)
  animate()
})

onUnmounted(() => {
  if (animId) cancelAnimationFrame(animId)
  window.removeEventListener('resize', resizeCanvas)
})

watch(effectiveAura, () => {
  particles = []
})
</script>

<template>
  <div
    ref="containerRef"
    :class="[
      'pixel-particles-wrapper',
      effectiveAura ? `pixel-aura--${effectiveAura}` : '',
    ]"
  >
    <canvas
      v-if="effectiveAura"
      ref="canvasRef"
      class="pixel-particles-canvas"
    />
    <div class="pixel-particles-content">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.pixel-particles-wrapper {
  position: relative;
  display: inline-flex;
}

.pixel-particles-canvas {
  position: absolute;
  top: -16px;
  left: -16px;
  pointer-events: none;
  z-index: 5;
  image-rendering: pixelated;
}

.pixel-particles-content {
  position: relative;
  z-index: 1;
}

.pixel-aura--gold .pixel-particles-content {
  filter: drop-shadow(0 0 6px rgba(251, 191, 36, 0.5));
}

.pixel-aura--silver .pixel-particles-content {
  filter: drop-shadow(0 0 6px rgba(226, 232, 240, 0.45));
}

.pixel-aura--bronze .pixel-particles-content {
  filter: drop-shadow(0 0 6px rgba(217, 119, 6, 0.5));
}
</style>
