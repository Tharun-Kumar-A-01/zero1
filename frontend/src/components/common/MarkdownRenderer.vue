<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
	content: string
}>()

function escapeHtml(text: string): string {
	return text
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&#039;')
}

const renderedHtml = computed(() => {
	if (!props.content) return ''

	const lines = props.content.split('\n')
	const output: string[] = []
	let inCodeBlock = false
	let codeBlockLang = ''
	let codeBuffer: string[] = []
	let inList = false
	let listType: 'ul' | 'ol' = 'ul'

	for (let i = 0; i < lines.length; i++) {
		const rawLine = lines[i] ?? ''
		const line = rawLine.trimEnd()

		// Code block toggle: ```lang
		if (line.trim().startsWith('```')) {
			if (inCodeBlock) {
				// End code block
				const escapedCode = escapeHtml(codeBuffer.join('\n'))
				output.push(
					`<pre class="rendered-code-block"><code class="language-${codeBlockLang}">${escapedCode}</code></pre>`
				)
				codeBuffer = []
				inCodeBlock = false
				codeBlockLang = ''
			} else {
				// Start code block
				if (inList) {
					output.push(listType === 'ul' ? '</ul>' : '</ol>')
					inList = false
				}
				inCodeBlock = true
				codeBlockLang = line.trim().slice(3).trim()
			}
			continue
		}

		if (inCodeBlock) {
			codeBuffer.push(rawLine)
			continue
		}

		// List items
		const isBullet = /^\s*[-*]\s+(.*)$/.exec(line)
		const isNumbered = /^\s*\d+\.\s+(.*)$/.exec(line)

		if (isBullet && isBullet[1] !== undefined) {
			if (!inList || listType !== 'ul') {
				if (inList) output.push(listType === 'ul' ? '</ul>' : '</ol>')
				output.push('<ul class="rendered-list">')
				inList = true
				listType = 'ul'
			}
			output.push(`<li>${formatInline(isBullet[1])}</li>`)
			continue
		} else if (isNumbered && isNumbered[1] !== undefined) {
			if (!inList || listType !== 'ol') {
				if (inList) output.push(listType === 'ul' ? '</ul>' : '</ol>')
				output.push('<ol class="rendered-list">')
				inList = true
				listType = 'ol'
			}
			output.push(`<li>${formatInline(isNumbered[1])}</li>`)
			continue
		} else if (inList) {
			output.push(listType === 'ul' ? '</ul>' : '</ol>')
			inList = false
		}

		// Empty line
		if (!line.trim()) {
			output.push('<div class="rendered-spacing"></div>')
			continue
		}

		// Headings
		if (line.startsWith('### ')) {
			output.push(`<h4 class="rendered-h3">${formatInline(line.slice(4))}</h4>`)
		} else if (line.startsWith('## ')) {
			output.push(`<h3 class="rendered-h2">${formatInline(line.slice(3))}</h3>`)
		} else if (line.startsWith('# ')) {
			output.push(`<h2 class="rendered-h1">${formatInline(line.slice(2))}</h2>`)
		} else {
			output.push(`<p class="rendered-p">${formatInline(line)}</p>`)
		}
	}

	if (inCodeBlock) {
		const escapedCode = escapeHtml(codeBuffer.join('\n'))
		output.push(`<pre class="rendered-code-block"><code>${escapedCode}</code></pre>`)
	}
	if (inList) {
		output.push(listType === 'ul' ? '</ul>' : '</ol>')
	}

	return output.join('\n')
})

function formatInline(text: string): string {
	let res = escapeHtml(text)

	// Inline code: `code`
	res = res.replace(/`([^`]+)`/g, '<code class="rendered-inline-code">$1</code>')

	// Bold: **text** or __text__
	res = res.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')

	// Italic: *text* or _text_
	res = res.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>')

	return res
}
</script>

<template>
	<div class="markdown-rendered-view" v-html="renderedHtml"></div>
</template>

<style>
/* Scoped styles applied to dynamically rendered markdown content */
.markdown-rendered-view {
	font-size: 0.95rem;
	line-height: 1.65;
	color: var(--va-text-primary);
}

.markdown-rendered-view .rendered-h1 {
	font-size: 1.3rem;
	font-weight: 700;
	margin: 1rem 0 0.5rem;
	color: var(--va-text-primary);
}

.markdown-rendered-view .rendered-h2 {
	font-size: 1.15rem;
	font-weight: 700;
	margin: 0.85rem 0 0.4rem;
	color: var(--va-text-primary);
}

.markdown-rendered-view .rendered-h3 {
	font-size: 1.02rem;
	font-weight: 700;
	margin: 0.75rem 0 0.35rem;
	color: var(--va-text-primary);
}

.markdown-rendered-view .rendered-p {
	margin: 0.4rem 0;
	color: var(--va-text-primary);
}

.markdown-rendered-view .rendered-spacing {
	height: 0.5rem;
}

.markdown-rendered-view .rendered-inline-code {
	background-color: var(--va-background-element);
	border: 1px solid var(--va-background-border);
	padding: 2px 6px;
	border-radius: 4px;
	font-family: 'JetBrains Mono', 'Fira Code', monospace;
	font-size: 0.88em;
	color: var(--va-primary);
}

.markdown-rendered-view .rendered-code-block {
	background-color: var(--va-background-element);
	border: 1px solid var(--va-background-border);
	border-radius: 6px;
	padding: 0.85rem 1rem;
	margin: 0.65rem 0;
	overflow-x: auto;
	font-family: 'JetBrains Mono', 'Fira Code', monospace;
	font-size: 0.86rem;
	line-height: 1.5;
}

.markdown-rendered-view .rendered-list {
	padding-left: 1.5rem;
	margin: 0.4rem 0;
}

.markdown-rendered-view .rendered-list li {
	margin-bottom: 0.25rem;
}
</style>
