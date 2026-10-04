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
					<VaIcon name="edit" size="14px" />
					Write
				</button>
				<button
					type="button"
					class="tab-btn"
					:class="{ active: activeTab === 'preview' }"
					@click="activeTab = 'preview'"
				>
					<VaIcon name="visibility" size="14px" />
					Preview
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
				<VaIcon name="format_bold" size="16px" />
			</button>
			<button
				type="button"
				class="toolbar-btn"
				title="Italic"
				@click="applyFormat('*', '*', 'italic text')"
			>
				<VaIcon name="format_italic" size="16px" />
			</button>
			<button
				type="button"
				class="toolbar-btn"
				title="Heading 3"
				@click="insertLinePrefix('### ')"
			>
				<VaIcon name="title" size="16px" />
			</button>
			<span class="toolbar-divider"></span>
			<button
				type="button"
				class="toolbar-btn"
				title="Inline Code"
				@click="applyFormat('`', '`', 'code')"
			>
				<VaIcon name="code" size="16px" />
			</button>
			<button
				type="button"
				class="toolbar-btn"
				title="Code Block"
				@click="applyFormat('```\n', '\n```', '// code block')"
			>
				<VaIcon name="integration_instructions" size="16px" />
			</button>
			<span class="toolbar-divider"></span>
			<button
				type="button"
				class="toolbar-btn"
				title="Bullet List"
				@click="insertLinePrefix('- ')"
			>
				<VaIcon name="format_list_bulleted" size="16px" />
			</button>
			<button
				type="button"
				class="toolbar-btn"
				title="Numbered List"
				@click="insertLinePrefix('1. ')"
			>
				<VaIcon name="format_list_numbered" size="16px" />
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
	border: 1px solid var(--va-background-border);
	border-radius: 4px;
	overflow: hidden;
	background-color: var(--va-background-primary);
}

.editor-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 0.5rem 0.75rem;
	background-color: var(--va-background-element);
	border-bottom: 1px solid var(--va-background-border);
}

.editor-label {
	font-size: 0.78rem;
	font-weight: 700;
	color: var(--va-text-secondary);
	text-transform: uppercase;
	letter-spacing: 0.04em;
}

.mode-tabs {
	display: flex;
	gap: 0.25rem;
	background-color: var(--va-background-primary);
	border: 1px solid var(--va-background-border);
	border-radius: 4px;
	padding: 2px;
}

.tab-btn {
	background: transparent;
	border: none;
	padding: 3px 8px;
	font-size: 0.75rem;
	font-weight: 600;
	color: var(--va-text-secondary);
	cursor: pointer;
	border-radius: 3px;
	display: flex;
	align-items: center;
	gap: 4px;
	transition: all 0.15s ease;
}

.tab-btn.active {
	background-color: var(--va-primary);
	color: #ffffff;
}

.toolbar {
	display: flex;
	align-items: center;
	gap: 0.25rem;
	padding: 0.35rem 0.75rem;
	border-bottom: 1px solid var(--va-background-border);
	background-color: var(--va-background-primary);
}

.toolbar-btn {
	background: transparent;
	border: none;
	border-radius: 4px;
	padding: 4px;
	cursor: pointer;
	color: var(--va-text-primary);
	display: flex;
	align-items: center;
	justify-content: center;
	transition: background 0.15s ease;
}

.toolbar-btn:hover {
	background-color: var(--va-background-element);
}

.toolbar-divider {
	width: 1px;
	height: 16px;
	background-color: var(--va-background-border);
	margin: 0 0.25rem;
}

.editor-content-area {
	min-height: 140px;
}

.editor-textarea {
	width: 100%;
	border: none;
	outline: none;
	padding: 0.75rem;
	font-family: inherit;
	font-size: 0.92rem;
	line-height: 1.6;
	color: var(--va-text-primary);
	background-color: transparent;
	resize: vertical;
	box-sizing: border-box;
}

.editor-preview-box {
	padding: 0.75rem;
	min-height: 140px;
	background-color: var(--va-background-primary);
}

.preview-empty-hint {
	font-size: 0.85rem;
	color: var(--va-text-secondary);
	font-style: italic;
	padding: 1.5rem 0;
	text-align: center;
}
</style>
