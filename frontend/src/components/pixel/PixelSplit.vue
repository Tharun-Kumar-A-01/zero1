<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
	modelValue?: number
	vertical?: boolean
	limits?: [number, number]
}

const props = withDefaults(defineProps<Props>(), {
	modelValue: 50,
	vertical: false,
	limits: () => [15, 15],
})

const emit = defineEmits<{
	(e: 'update:modelValue', val: number): void
}>()

const containerRef = ref<HTMLDivElement | null>(null)
const isDragging = ref(false)

const splitPercent = computed(() => {
	const min = props.limits[0]
	const max = 100 - props.limits[1]
	return Math.min(max, Math.max(min, props.modelValue))
})

const startDrag = (e: MouseEvent) => {
	e.preventDefault()
	isDragging.value = true

	const onMouseMove = (moveEvent: MouseEvent) => {
		if (!containerRef.value) return
		const rect = containerRef.value.getBoundingClientRect()
		let percent = 50

		if (props.vertical) {
			const offset = moveEvent.clientY - rect.top
			percent = (offset / rect.height) * 100
		} else {
			const offset = moveEvent.clientX - rect.left
			percent = (offset / rect.width) * 100
		}

		const min = props.limits[0]
		const max = 100 - props.limits[1]
		const clamped = Math.min(max, Math.max(min, percent))
		emit('update:modelValue', Math.round(clamped))
	}

	const onMouseUp = () => {
		isDragging.value = false
		window.removeEventListener('mousemove', onMouseMove)
		window.removeEventListener('mouseup', onMouseUp)
	}

	window.addEventListener('mousemove', onMouseMove)
	window.addEventListener('mouseup', onMouseUp)
}
</script>

<template>
	<div
		ref="containerRef"
		:class="[
			'pixel-split',
			props.vertical ? 'pixel-split--vertical' : 'pixel-split--horizontal',
			{ 'is-dragging': isDragging },
		]"
	>
		<div
			class="pixel-split__pane start-pane"
			:style="props.vertical ? { height: `${splitPercent}%` } : { width: `${splitPercent}%` }"
		>
			<slot name="start" />
		</div>

		<div class="pixel-split__gutter" @mousedown="startDrag">
			<div class="gutter-handle" />
		</div>

		<div
			class="pixel-split__pane end-pane"
			:style="
				props.vertical
					? { height: `${100 - splitPercent}%` }
					: { width: `${100 - splitPercent}%` }
			"
		>
			<slot name="end" />
		</div>
	</div>
</template>

<style scoped>
.pixel-split {
	display: flex;
	width: 100%;
	height: 100%;
	overflow: hidden;
	position: relative;
}

.pixel-split--horizontal {
	flex-direction: row;
}

.pixel-split--vertical {
	flex-direction: column;
}

.pixel-split__pane {
	overflow: hidden;
	position: relative;
}

.pixel-split__gutter {
	background-color: var(--pixel-border);
	position: relative;
	flex-shrink: 0;
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 5;
	transition: background-color 0.15s;
}

.pixel-split--horizontal > .pixel-split__gutter {
	width: 6px;
	cursor: col-resize;
}

.pixel-split--vertical > .pixel-split__gutter {
	height: 6px;
	cursor: row-resize;
}

.pixel-split__gutter:hover,
.is-dragging .pixel-split__gutter {
	background-color: var(--pixel-btn-primary-bg);
}

.gutter-handle {
	background-color: var(--pixel-text-dim);
	border-radius: 1px;
}

.pixel-split--horizontal .gutter-handle {
	width: 2px;
	height: 24px;
}

.pixel-split--vertical .gutter-handle {
	width: 24px;
	height: 2px;
}

.is-dragging {
	user-select: none;
}
</style>
