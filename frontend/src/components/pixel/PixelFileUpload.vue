<script setup lang="ts">
import { ref } from 'vue'
import PixelIcon from './PixelIcon.vue'

interface Props {
	modelValue?: File | File[] | null
	dropzone?: boolean
	fileTypes?: string
	type?: 'single' | 'multiple'
}

const props = withDefaults(defineProps<Props>(), {
	dropzone: true,
	type: 'single',
})

const emit = defineEmits<{
	(e: 'update:modelValue', files: File | File[] | null): void
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)
const isDraggingOver = ref(false)

const triggerBrowse = () => {
	fileInputRef.value?.click()
}

const handleFileChange = (e: Event) => {
	const target = e.target as HTMLInputElement
	if (!target.files || target.files.length === 0) {
		emit('update:modelValue', null)
		return
	}

	if (props.type === 'single') {
		emit('update:modelValue', target.files[0] ?? null)
	} else {
		emit('update:modelValue', Array.from(target.files))
	}
}

const handleDrop = (e: DragEvent) => {
	e.preventDefault()
	isDraggingOver.value = false

	if (!e.dataTransfer?.files || e.dataTransfer.files.length === 0) return

	if (props.type === 'single') {
		emit('update:modelValue', e.dataTransfer.files[0] ?? null)
	} else {
		emit('update:modelValue', Array.from(e.dataTransfer.files))
	}
}

const getFileName = () => {
	if (!props.modelValue) return null
	if (Array.isArray(props.modelValue)) {
		return props.modelValue.length > 0 ? `${props.modelValue.length} files selected` : null
	}
	return props.modelValue.name
}
</script>

<template>
	<div
		:class="['pixel-file-upload', { 'is-dragover': isDraggingOver }]"
		@dragover.prevent="isDraggingOver = true"
		@dragleave.prevent="isDraggingOver = false"
		@drop="handleDrop"
		@click="triggerBrowse"
	>
		<input
			ref="fileInputRef"
			type="file"
			:accept="fileTypes"
			:multiple="type === 'multiple'"
			class="pixel-hidden-input"
			@change="handleFileChange"
		/>

		<div class="upload-content">
			<div class="upload-icon-box">
				<PixelIcon name="upload" :size="24" />
			</div>

			<div v-if="getFileName()" class="selected-file-info">
				<span class="file-name">{{ getFileName() }}</span>
				<span class="file-hint">Click or drop to replace</span>
			</div>
			<div v-else class="upload-prompt">
				<span class="prompt-main">Drag and drop file here, or click to browse</span>
				<span v-if="fileTypes" class="prompt-sub">Accepted: {{ fileTypes }}</span>
			</div>
		</div>
	</div>
</template>

<style scoped>
.pixel-file-upload {
	border: 2px dashed var(--pixel-border);
	background-color: var(--pixel-bg-alt);
	box-shadow: inset 0 2px 0 0 rgba(0, 0, 0, 0.4);
	border-radius: 4px;
	padding: 24px 16px;
	text-align: center;
	cursor: pointer;
	transition: all 0.15s ease;
	user-select: none;
}

.pixel-file-upload:hover,
.is-dragover {
	border-color: var(--pixel-btn-primary-bg);
	background-color: rgba(90, 50, 163, 0.1);
}

.pixel-hidden-input {
	display: none;
}

.upload-content {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 8px;
}

.upload-icon-box {
	color: var(--pixel-text-dim);
}

.pixel-file-upload:hover .upload-icon-box {
	color: var(--pixel-btn-primary-hover);
}

.prompt-main {
	font-family: var(--font-pixel);
	font-size: 12px;
	color: var(--pixel-text);
	display: block;
}

.prompt-sub {
	font-size: 11px;
	color: var(--pixel-text-dim);
	display: block;
	margin-top: 2px;
}

.selected-file-info {
	display: flex;
	flex-direction: column;
	gap: 2px;
}

.file-name {
	font-family: var(--font-mono);
	font-size: 13px;
	color: #34d399;
	font-weight: 600;
}

.file-hint {
	font-size: 11px;
	color: var(--pixel-text-dim);
}
</style>
