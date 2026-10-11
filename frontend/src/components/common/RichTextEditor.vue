<script setup lang="ts">
import { ref } from 'vue'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'

const props = withDefaults(
	defineProps<{
		modelValue: string
		label?: string
		placeholder?: string
		rows?: number
		required?: boolean
	}>(),
	{
		label: 'Problem Statement (Rich Text / Markdown)',
		placeholder: 'Write the problem description using markdown...',
		rows: 6,
		required: false,
	}
)

const emit = defineEmits<{
	(e: 'update:modelValue', val: string): void
}>()

const activeTab = ref<'write' | 'preview'>('write')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

function applyFormat(prefix: string, suffix: string = '', defaultText: string = ''): void {
	const el = textareaRef.value
	if (!el) return

	const start = el.selectionStart
	const end = el.selectionEnd
	const text = props.modelValue || ''

	const selected = text.slice(start, end) || defaultText
	const replacement = `${prefix}${selected}${suffix}`
	const updated = text.slice(0, start) + replacement + text.slice(end)

	emit('update:modelValue', updated)

	// Set cursor position after update
	setTimeout(() => {
		el.focus()
		el.setSelectionRange(start + prefix.length, start + prefix.length + selected.length)
	}, 10)
}

function insertLinePrefix(prefix: string): void {
	const el = textareaRef.value
	if (!el) return

	const start = el.selectionStart
	const text = props.modelValue || ''

	// Find beginning of current line
	const lastNewline = text.lastIndexOf('\n', start - 1)
	const lineStart = lastNewline === -1 ? 0 : lastNewline + 1

	const updated = text.slice(0, lineStart) + prefix + text.slice(lineStart)
	emit('update:modelValue', updated)

	setTimeout(() => {
		el.focus()
		el.setSelectionRange(start + prefix.length, start + prefix.length)
	}, 10)
}
</script>

<template>
	<div class="rich-text-editor">
		<div class="editor-header">
			<label class="editor-label">{{ label }}</label>
			<div class="mode-tabs">
				<button
					type="button"
					class="tab-btn"
					:class="{ active: activeTab === 'write' }"
					@click="activeTab = 'write'"
				>
					<PixelIcon name="edit" :size="12" />
					<span>Write</span>
				</button>
				<button
					type="button"
					class="tab-btn"
					:class="{ active: activeTab === 'preview' }"
					@click="activeTab = 'preview'"
				>
					<PixelIcon name="visibility" :size="12" />
					<span>Preview</span>
				</button>
			</div>
		</div>

		<!-- Toolbar (Active only in write mode) -->
		<div v-show="activeTab === 'write'" class="toolbar">
			<button
				type="button"
				class="toolbar-btn"
				title="Bold"
				@click="applyFormat('**', '**', 'bold text')"
			>
				<span class="text-icon text-bold">B</span>
			</button>
			<button
				type="button"
				class="toolbar-btn"
				title="Italic"
				@click="applyFormat('*', '*', 'italic text')"
			>
				<span class="text-icon text-italic">I</span>
			</button>
			<button
				type="button"
				class="toolbar-btn"
				title="Heading 3"
				@click="insertLinePrefix('### ')"
			>
				<span class="text-icon text-heading">H3</span>
			</button>
			<span class="toolbar-divider"></span>
			<button
				type="button"
				class="toolbar-btn"
				title="Inline Code"
				@click="applyFormat('`', '`', 'code')"
			>
				<PixelIcon name="code" :size="13" />
			</button>
			<button
				type="button"
				class="toolbar-btn"
				title="Code Block"
				@click="applyFormat('```\n', '\n```', '// code block')"
			>
				<PixelIcon name="terminal" :size="13" />
			</button>
			<span class="toolbar-divider"></span>
			<button
				type="button"
				class="toolbar-btn"
				title="Bullet List"
				@click="insertLinePrefix('- ')"
			>
				<PixelIcon name="list" :size="13" />
			</button>
			<button
				type="button"
				class="toolbar-btn"
				title="Numbered List"
				@click="insertLinePrefix('1. ')"
			>
				<span class="text-icon text-numlist">1.</span>
			</button>
		</div>

		<!-- Input Area -->
		<div class="editor-content-area">
			<textarea
				v-show="activeTab === 'write'"
				ref="textareaRef"
				class="editor-textarea"
				:value="modelValue"
				:placeholder="placeholder"
				:rows="rows"
				:required="required"
				@input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
			></textarea>

			<!-- Live Markdown Preview -->
			<div v-show="activeTab === 'preview'" class="editor-preview-box">
				<MarkdownRenderer
					v-if="modelValue.trim()"
					:content="modelValue"
				/>
				<div v-else class="preview-empty-hint">
					Nothing to preview yet. Switch to Write mode to author content.
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped>
.rich-text-editor {
	display: flex;
	flex-direction: column;
	border: 2px solid var(--pixel-border);
	border-radius: 2px;
	box-shadow: 0 4px 0 0 var(--pixel-border-dark);
	background-color: var(--pixel-surface);
	overflow: hidden;
}

.editor-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 6px 10px;
	background-color: var(--pixel-surface-alt);
	border-bottom: 2px solid var(--pixel-border);
}

.editor-label {
	font-family: var(--font-pixel);
	font-size: 11px;
	font-weight: 700;
	color: var(--pixel-text-muted);
	text-transform: uppercase;
	letter-spacing: 0.05em;
}

.mode-tabs {
	display: flex;
	gap: 4px;
	background-color: var(--pixel-bg-alt);
	border: 1px solid var(--pixel-border);
	border-radius: 2px;
	padding: 2px;
}

.tab-btn {
	background: transparent;
	border: 1px solid transparent;
	padding: 3px 8px;
	font-family: var(--font-pixel);
	font-size: 11px;
	font-weight: 600;
	color: var(--pixel-text-muted);
	cursor: pointer;
	border-radius: 2px;
	display: flex;
	align-items: center;
	gap: 5px;
	transition: all 0.1s ease;
}

.tab-btn:hover {
	color: var(--pixel-text);
	background-color: var(--pixel-surface-raised);
}

.tab-btn.active {
	background-color: var(--pixel-btn-primary-bg);
	border-color: var(--pixel-btn-primary-border);
	color: var(--pixel-btn-primary-text);
	box-shadow: inset 0 -2px 0 0 var(--pixel-btn-primary-shade);
}

.toolbar {
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	gap: 4px;
	padding: 6px 10px;
	border-bottom: 2px solid var(--pixel-border);
	background-color: var(--pixel-surface);
}

.toolbar-btn {
	background: var(--pixel-surface-alt);
	border: 1px solid var(--pixel-border);
	border-radius: 2px;
	padding: 3px 7px;
	min-width: 28px;
	height: 26px;
	cursor: pointer;
	color: var(--pixel-text);
	display: inline-flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 2px 0 0 var(--pixel-border-dark);
	transition: all 0.1s ease;
}

.toolbar-btn:hover {
	background-color: var(--pixel-surface-raised);
	border-color: var(--pixel-border-bright);
	color: #ffffff;
}

.toolbar-btn:active {
	transform: translateY(2px);
	box-shadow: none;
}

.text-icon {
	font-family: var(--font-pixel);
	font-size: 12px;
	line-height: 1;
}

.text-bold {
	font-weight: 800;
}

.text-italic {
	font-style: italic;
	font-weight: 700;
}

.text-heading {
	font-weight: 800;
	font-size: 10px;
}

.text-numlist {
	font-size: 11px;
	font-weight: 700;
}

.toolbar-divider {
	width: 2px;
	height: 18px;
	background-color: var(--pixel-border);
	margin: 0 4px;
}

.editor-content-area {
	min-height: 140px;
	background-color: var(--pixel-bg-alt);
}

.editor-textarea {
	width: 100%;
	border: none;
	outline: none;
	padding: 10px 12px;
	font-family: var(--font-mono);
	font-size: 13px;
	line-height: 1.6;
	color: var(--pixel-text);
	caret-color: #fbbf24;
	background-color: var(--pixel-bg-alt);
	resize: vertical;
	box-sizing: border-box;
}

.editor-textarea:focus {
	background-color: #110e19;
}

.editor-textarea::placeholder {
	color: var(--pixel-text-dim);
}

.editor-preview-box {
	padding: 12px;
	min-height: 140px;
	background-color: var(--pixel-bg-alt);
	color: var(--pixel-text);
}

.preview-empty-hint {
	font-family: var(--font-pixel);
	font-size: 12px;
	color: var(--pixel-text-dim);
	font-style: italic;
	padding: 2rem 0;
	text-align: center;
}
</style>
