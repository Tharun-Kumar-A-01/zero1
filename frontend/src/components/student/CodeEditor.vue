<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import Prism from 'prismjs'
import 'prismjs/components/prism-c'
import 'prismjs/components/prism-cpp'
import 'prismjs/components/prism-python'
import 'prismjs/components/prism-java'
import '@/assets/base16-default-dark.css'

const props = defineProps<{
	modelValue: string
	language: string
	allowedLanguages?: string[]
	starterTemplates?: Record<string, string>
}>()

const emit = defineEmits<{
	(e: 'update:modelValue', val: string): void
	(e: 'update:language', val: string): void
	(e: 'reset-code'): void
}>()

const textareaRef = ref<HTMLTextAreaElement | null>(null)
const preRef = ref<HTMLElement | null>(null)
const gutterRef = ref<HTMLElement | null>(null)
const dropdownRef = ref<HTMLElement | null>(null)
const isDropdownOpen = ref<boolean>(false)

const languageOptions = [
	{ label: 'Python 3', value: 'python' },
	{ label: 'C++ 17', value: 'cpp' },
	{ label: 'Java 17', value: 'java' },
	{ label: 'C', value: 'c' },
]

const filteredLanguageOptions = computed(() => {
	if (!props.allowedLanguages || props.allowedLanguages.length === 0) {
		return languageOptions
	}
	const allowed = props.allowedLanguages.map((l) => l.toLowerCase())
	const filtered = languageOptions.filter((opt) => {
		if (allowed.includes(opt.value)) return true
		if (opt.value === 'cpp' && (allowed.includes('c++') || allowed.includes('cpp'))) return true
		return false
	})
	return filtered.length > 0 ? filtered : languageOptions
})

const currentLanguageLabel = computed<string>(() => {
	const current = props.language.toLowerCase()
	const target = current === 'c++' ? 'cpp' : current
	const match = languageOptions.find((l) => l.value === target)
	return match ? match.label : props.language
})

const lineCount = computed<number>(() => {
	const lines = (props.modelValue || '').split('\n').length
	return Math.max(lines, 1)
})

function toggleDropdown(): void {
	isDropdownOpen.value = !isDropdownOpen.value
}

function selectOption(val: string): void {
	handleLanguageChange(val)
	isDropdownOpen.value = false
}

function handleDocClick(e: MouseEvent): void {
	if (dropdownRef.value && !dropdownRef.value.contains(e.target as Node)) {
		isDropdownOpen.value = false
	}
}

onMounted(() => {
	document.addEventListener('click', handleDocClick)
})

onUnmounted(() => {
	document.removeEventListener('click', handleDocClick)
})

function handleScroll(): void {
	if (!textareaRef.value) return
	const { scrollTop, scrollLeft } = textareaRef.value
	if (preRef.value) {
		preRef.value.scrollTop = scrollTop
		preRef.value.scrollLeft = scrollLeft
	}
	if (gutterRef.value) {
		gutterRef.value.scrollTop = scrollTop
	}
}

function handleInput(e: Event): void {
	const val = (e.target as HTMLTextAreaElement).value
	emit('update:modelValue', val)
}

function handleKeydown(e: KeyboardEvent): void {
	const textarea = textareaRef.value
	if (!textarea) return

	if (e.key === 'Tab') {
		e.preventDefault()
		const start = textarea.selectionStart
		const end = textarea.selectionEnd
		const val = props.modelValue
		const nextVal = val.substring(0, start) + '    ' + val.substring(end)
		emit('update:modelValue', nextVal)
		nextTick(() => {
			textarea.selectionStart = textarea.selectionEnd = start + 4
		})
		return
	}

	// Auto-closing brackets and quotes
	const pairs: Record<string, string> = {
		'(': ')',
		'[': ']',
		'{': '}',
		'"': '"',
		"'": "'",
		'`': '`',
	}

	if (pairs[e.key]) {
		const start = textarea.selectionStart
		const end = textarea.selectionEnd
		if (start === end) {
			const closeChar = pairs[e.key]!
			e.preventDefault()
			const val = props.modelValue
			const nextVal = val.substring(0, start) + e.key + closeChar + val.substring(end)
			emit('update:modelValue', nextVal)
			nextTick(() => {
				textarea.selectionStart = textarea.selectionEnd = start + 1
			})
		}
	}
}

function handleLanguageChange(newLang: unknown): void {
	let val = ''
	if (typeof newLang === 'string') {
		val = newLang
	} else if (newLang && typeof newLang === 'object' && 'value' in newLang) {
		val = String((newLang as { value: unknown }).value)
	} else if (newLang) {
		val = String(newLang)
	}
	if (val) {
		val = val.toLowerCase()
		if (val === 'c++') val = 'cpp'
		emit('update:language', val)
	}
}

function handleReset(): void {
	emit('reset-code')
}

const highlightedCode = computed<string>(() => {
	const code = props.modelValue || ''
	if (!code) return '&nbsp;'

	let lang = props.language.toLowerCase()
	if (lang === 'c++') lang = 'cpp'
	if (lang === 'py') lang = 'python'

	const grammar = Prism.languages[lang] || Prism.languages.clike || Prism.languages.plain || {}
	try {
		const highlighted = Prism.highlight(code, grammar, lang)
		return highlighted + (code.endsWith('\n') ? ' ' : '')
	} catch {
		return Prism.util.encode(code) as string
	}
})

watch(
	() => props.modelValue,
	() => {
		handleScroll()
	}
)
</script>

<template>
	<div class="code-editor-container">
		<!-- Editor Top Toolbar -->
		<div class="editor-header-bar">
			<div class="editor-left-tools">
				<!-- Custom Language Dropdown: Pointer cursor, instant mouse click handling, high z-index -->
				<div class="lang-selector-container" ref="dropdownRef">
					<button
						type="button"
						class="lang-dropdown-trigger"
						:class="{ open: isDropdownOpen }"
						aria-haspopup="listbox"
						:aria-expanded="isDropdownOpen"
						@click="toggleDropdown"
					>
						<span class="lang-selected-label">{{ currentLanguageLabel }}</span>
						<svg class="dropdown-chevron" :class="{ rotated: isDropdownOpen }" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.06 1.06l-4.24 4.25a.75.75 0 01-1.06 0L5.21 8.27a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
						</svg>
					</button>

					<div
						v-if="isDropdownOpen"
						class="lang-dropdown-menu"
						role="listbox"
					>
						<button
							v-for="opt in filteredLanguageOptions"
							:key="opt.value"
							type="button"
							role="option"
							:aria-selected="opt.value === language"
							class="lang-dropdown-item"
							:class="{ active: opt.value === language }"
							@mousedown.prevent
							@click="selectOption(opt.value)"
						>
							<span class="option-name">{{ opt.label }}</span>
							<svg v-if="opt.value === language" class="check-icon" viewBox="0 0 20 20" fill="currentColor">
								<path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" />
							</svg>
						</button>
					</div>
				</div>

				<span class="tab-note">Tab: 4 spaces</span>
			</div>

			<div class="editor-right-tools">
				<VaButton
					preset="secondary"
					size="small"
					icon="restart_alt"
					title="Reset to boilerplate template"
					@click="handleReset"
				>
					Reset Code
				</VaButton>
			</div>
		</div>

		<!-- Workspace Body with Line Gutter and Highlighted Code Area -->
		<div class="editor-body">
			<!-- Line Numbers Gutter -->
			<div ref="gutterRef" class="line-gutter">
				<div
					v-for="n in lineCount"
					:key="n"
					class="line-num"
				>
					{{ n }}
				</div>
			</div>

			<!-- Editor Textarea and Highlighting Pre -->
			<div class="editor-canvas">
				<pre
					ref="preRef"
					class="syntax-overlay"
					aria-hidden="true"
					v-html="highlightedCode"
				/>
				<textarea
					ref="textareaRef"
					:value="modelValue"
					class="code-input"
					spellcheck="false"
					autocapitalize="off"
					autocomplete="off"
					placeholder="Write your solution here..."
					@input="handleInput"
					@keydown="handleKeydown"
					@scroll="handleScroll"
				/>
			</div>
		</div>
	</div>
</template>

<style scoped>
.code-editor-container {
	display: flex;
	flex-direction: column;
	height: 100%;
	width: 100%;
	background: #181818;
	overflow: hidden;
	font-family: 'JetBrains Mono', monospace !important;
}

.editor-header-bar {
	position: relative;
	z-index: 50;
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0.5rem 0.85rem;
	background: #1f1f1f;
	border-bottom: 1px solid #282828;
	flex-shrink: 0;
}

.editor-left-tools {
	display: flex;
	align-items: center;
	gap: 0.85rem;
}

.lang-selector-container {
	position: relative;
	display: inline-block;
}

.lang-dropdown-trigger {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.5rem;
	min-width: 130px;
	height: 32px;
	padding: 0 0.75rem;
	background: #2a2a2a;
	color: #e0e0e0;
	border: 1px solid #3d3d3d;
	border-radius: 4px;
	font-family: 'JetBrains Mono', monospace !important;
	font-size: 0.8125rem;
	font-weight: 500;
	cursor: pointer !important;
	user-select: none;
	transition: background 0.15s, border-color 0.15s;
}

.lang-dropdown-trigger:hover {
	background: #333333;
	border-color: #505050;
}

.lang-dropdown-trigger.open {
	border-color: #2563eb;
	box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
}

.dropdown-chevron {
	width: 16px;
	height: 16px;
	color: #999;
	transition: transform 0.2s;
	flex-shrink: 0;
}

.dropdown-chevron.rotated {
	transform: rotate(180deg);
}

.lang-dropdown-menu {
	position: absolute;
	top: calc(100% + 4px);
	left: 0;
	z-index: 100;
	min-width: 140px;
	background: #242424;
	border: 1px solid #383838;
	border-radius: 6px;
	box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
	padding: 4px;
	display: flex;
	flex-direction: column;
	gap: 2px;
}

.lang-dropdown-item {
	display: flex;
	align-items: center;
	justify-content: space-between;
	width: 100%;
	padding: 0.45rem 0.65rem;
	background: transparent;
	border: none;
	border-radius: 4px;
	color: #d0d0d0;
	font-family: 'JetBrains Mono', monospace !important;
	font-size: 0.8125rem;
	text-align: left;
	cursor: pointer !important;
	user-select: none;
	transition: background 0.15s, color 0.15s;
}

.lang-dropdown-item:hover {
	background: #333333;
	color: #ffffff;
}

.lang-dropdown-item.active {
	background: #1e3a5f;
	color: #60a5fa;
	font-weight: 600;
}

.check-icon {
	width: 14px;
	height: 14px;
	color: #60a5fa;
	flex-shrink: 0;
}

.tab-note {
	font-size: 0.75rem;
	color: #b8b8b8;
}

.editor-right-tools {
	display: flex;
	align-items: center;
	gap: 0.5rem;
}

.editor-body {
	display: flex;
	flex-grow: 1;
	height: calc(100% - 46px);
	position: relative;
	overflow: hidden;
	font-family: 'JetBrains Mono', monospace !important;
	background: #181818;
}

.line-gutter {
	width: 46px;
	padding: 0.85rem 0.5rem 0.85rem 0;
	background: #181818;
	border-right: 1px solid #282828;
	text-align: right;
	user-select: none;
	overflow: hidden;
	flex-shrink: 0;
	font-family: 'JetBrains Mono', monospace !important;
	font-size: 0.875rem !important;
	line-height: 1.6rem !important;
	color: #585858;
}

.line-num {
	height: 1.6rem;
	font-family: 'JetBrains Mono', monospace !important;
	line-height: 1.6rem;
}

.editor-canvas {
	position: relative;
	flex-grow: 1;
	height: 100%;
	overflow: hidden;
	background: #181818;
	font-family: 'JetBrains Mono', monospace !important;
}

.syntax-overlay,
.code-input {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	margin: 0;
	padding: 0.85rem 1rem;
	width: 100%;
	height: 100%;
	font-family: 'JetBrains Mono', monospace !important;
	font-size: 0.875rem !important;
	line-height: 1.6rem !important;
	letter-spacing: 0 !important;
	font-variant-ligatures: none !important;
	-webkit-font-variant-ligatures: none !important;
	font-feature-settings: 'liga' 0, 'calt' 0, 'dlig' 0 !important;
	white-space: pre !important;
	word-wrap: normal !important;
	tab-size: 4 !important;
	-moz-tab-size: 4 !important;
	box-sizing: border-box !important;
	-webkit-font-smoothing: antialiased;
}

.syntax-overlay {
	z-index: 1;
	pointer-events: none;
	overflow: hidden;
	color: #d8d8d8;
	background: #181818;
	border: none;
}

.syntax-overlay * {
	font-family: 'JetBrains Mono', monospace !important;
}

.code-input {
	z-index: 2;
	background: transparent;
	color: transparent;
	caret-color: #f8f8f8;
	border: none;
	outline: none;
	resize: none;
	overflow: auto;
}

.code-input::selection {
	background: #383838 !important;
	color: #f8f8f8 !important;
}
</style>
