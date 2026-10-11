<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import PixelSprite from './PixelSprite.vue'

interface Props {
  active?: boolean
  ignite?: boolean
  size?: number
}

const props = withDefaults(defineProps<Props>(), {
  active: true,
  ignite: false,
  size: 32,
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
let animId: number | null = null

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  alpha: number
  color: string
}

let particles: Particle[] = []

const COLORS = ['#fef08a', '#facc15', '#f97316', '#dc2626', '#b91c1c']

function spawnParticle(isBurst = false) {
  if (!canvasRef.value) return
  const w = canvasRef.value.width
  const h = canvasRef.value.height

  const p: Particle = {
    x: w / 2 + (Math.random() - 0.5) * (w * 0.4),
    y: h * 0.7 + Math.random() * 4,
    vx: (Math.random() - 0.5) * (isBurst ? 2.5 : 1.0),
    vy: - (Math.random() * (isBurst ? 3.5 : 1.8) + 0.8),
    size: Math.random() > 0.6 ? 4 : 3,
    alpha: 1,
    color: COLORS[Math.floor(Math.random() * COLORS.length)] ?? '#f97316',
  }
  particles.push(p)
}

function triggerIgnition() {
  for (let i = 0; i < 24; i++) {
    spawnParticle(true)
  }
}

function animate() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, canvas.width, canvas.height)

  // Continuously spawn if active
  if (props.active && Math.random() < 0.4) {
    spawnParticle(false)
  }

  // Update & draw particles
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i]
    if (!p) continue
    p.x += p.vx
    p.y += p.vy
    p.alpha -= 0.025

    if (p.alpha <= 0 || p.y < 0) {
      particles.splice(i, 1)
      continue
    }

    ctx.fillStyle = p.color
    ctx.globalAlpha = Math.max(0, p.alpha)
    // Draw snap-to-grid pixel square
    const px = Math.round(p.x)
    const py = Math.round(p.y)
    ctx.fillRect(px, py, p.size, p.size)
  }

  ctx.globalAlpha = 1
  animId = requestAnimationFrame(animate)
}

watch(
  () => props.ignite,
  (val) => {
    if (val) triggerIgnition()
  },
)

onMounted(() => {
  if (canvasRef.value) {
    canvasRef.value.width = props.size * 1.5
    canvasRef.value.height = props.size * 2
  }
  if (props.ignite) {
    triggerIgnition()
  }
  animate()
})

onUnmounted(() => {
  if (animId) cancelAnimationFrame(animId)
})
</script>

<template>
  <div
    class="pixel-flame-container"
    :style="{ width: `${size}px`, height: `${size}px` }"
  >
    <canvas
      refCanvas="canvasRef"
      ref="canvasRef"
      class="pixel-flame-canvas"
    />
    <div :class="['pixel-flame-sprite-wrap', { 'flame-flicker': active }]">
      <PixelSprite name="flame" :size="size" />
    </div>
  </div>
</template>

<style scoped>
.pixel-flame-container {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.pixel-flame-canvas {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  pointer-events: none;
  z-index: 2;
  image-rendering: pixelated;
}

.pixel-flame-sprite-wrap {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.flame-flicker {
  animation: pixelFlicker 0.6s steps(2, start) infinite;
}

@keyframes pixelFlicker {
  0% {
    transform: scale(1) translateY(0);
    filter: drop-shadow(0 0 3px rgba(249, 115, 22, 0.7));
  }
  50% {
    transform: scale(1.06) translateY(-1px);
    filter: drop-shadow(0 0 6px rgba(234, 88, 12, 0.9));
  }
  100% {
    transform: scale(1) translateY(0);
    filter: drop-shadow(0 0 3px rgba(249, 115, 22, 0.7));
  }
}
</style>
