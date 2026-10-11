<script setup lang="ts">
import { computed } from 'vue'
import * as charm from 'charm-icons'

interface Props {
	name: string
	size?: number | string
	color?: string
}

const props = withDefaults(defineProps<Props>(), {
	size: 16,
	color: 'currentColor',
})

// Normalization alias dictionary to charm-icons keys
const ALIAS_MAP: Record<string, string> = {
	trash: 'Bin',
	bin: 'Bin',
	delete: 'Bin',
	remove: 'Bin',
	check: 'Tick',
	tick: 'Tick',
	done: 'Tick',
	success: 'Tick',
	check_circle: 'CircleTick',
	close: 'Cross',
	cross: 'Cross',
	x: 'Cross',
	cancel: 'Cross',
	plus: 'Plus',
	add: 'Plus',
	minus: 'Minus',
	search: 'Search',
	edit: 'Pencil',
	pencil: 'Pencil',
	copy: 'Copy',
	refresh: 'Refresh',
	sync: 'Refresh',
	reload: 'Refresh',
	flame: 'Flame',
	fire: 'Flame',
	trophy: 'Trophy',
	star: 'Star',
	heart: 'Heart',
	shield: 'Shield',
	sword: 'Sword',
	eye: 'Eye',
	info: 'Info',
	warning: 'CircleWarning',
	alert: 'CircleWarning',
	circle_warning: 'CircleWarning',
	user: 'Person',
	person: 'Person',
	person_add: 'Person',
	user_add: 'Person',
	users: 'People',
	people: 'People',
	upload: 'Upload',
	upload_file: 'Upload',
	import: 'Upload',
	download: 'Download',
	logout: 'SignOut',
	signout: 'SignOut',
	exit: 'SignOut',
	login: 'SignIn',
	signin: 'SignIn',
	settings: 'Cog',
	cog: 'Cog',
	code: 'Code',
	terminal: 'Terminal',
	clock: 'Clock',
	time: 'Clock',
	schedule: 'Clock',
	calendar: 'Calendar',
	calendar_today: 'Calendar',
	date_range: 'Calendar',
	event: 'Calendar',
	event_busy: 'Calendar',
	beach_access: 'TreeFir',
	school: 'GraduateCap',
	storage: 'Database',
	database: 'Database',
	filter: 'Filter',
	sort: 'SwapVertical',
	chevron_down: 'ChevronDown',
	'chevron-down': 'ChevronDown',
	chevron_up: 'ChevronUp',
	'chevron-up': 'ChevronUp',
	chevron_left: 'ChevronLeft',
	'chevron-left': 'ChevronLeft',
	chevron_right: 'ChevronRight',
	'chevron-right': 'ChevronRight',
	arrow_down: 'ArrowDown',
	'arrow-down': 'ArrowDown',
	arrow_up: 'ArrowUp',
	'arrow-up': 'ArrowUp',
	arrow_left: 'ArrowLeft',
	'arrow-left': 'ArrowLeft',
	arrow_right: 'ArrowRight',
	'arrow-right': 'ArrowRight',
	external: 'LinkExternal',
	'external-link': 'LinkExternal',
	link: 'Link',
	menu: 'MenuHamburger',
	hamburger: 'MenuHamburger',
	unfold_more: 'ChevronsUpDown',
	book: 'BookOpen',
	file: 'File',
	folder: 'Folder',
	play: 'MediaPlay',
	play_arrow: 'MediaPlay',
	pause: 'MediaPause',
	bell: 'Bell',
	help: 'Help',
	lock: 'Padlock',
	unlock: 'Padlock',
	visibility: 'Eye',
	format_bold: 'Notes',
	format_italic: 'Notes',
	title: 'Hash',
	heading: 'Hash',
	integration_instructions: 'Terminal',
	format_list_bulleted: 'LayoutList',
	format_list_numbered: 'LayoutList',
	list: 'LayoutList',
	auto_awesome: 'LightningBolt',
}

const charmMap = charm as unknown as Record<string, { paths: string }>

const iconPath = computed(() => {
	const raw = props.name.trim()
	if (!raw) return ''

	if (ALIAS_MAP[raw]) {
		const key = ALIAS_MAP[raw]
		if (charmMap[key]) return charmMap[key].paths
	}

	// Try PascalCase transformation (e.g. chevron-down -> ChevronDown)
	const pascal = raw
		.split(/[-_]/)
		.map((s) => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase())
		.join('')

	if (charmMap[pascal]) return charmMap[pascal].paths

	// Try direct match
	if (charmMap[raw]) return charmMap[raw].paths

	// If not found, return empty string — NEVER fall back to Star!
	return ''
})

const numericSize = computed(() => {
	if (props.size === 'small') return '12px'
	if (props.size === 'medium') return '16px'
	if (props.size === 'large') return '24px'
	if (typeof props.size === 'number') return `${props.size}px`
	if (typeof props.size === 'string') {
		const trimmed = props.size.trim()
		if (trimmed.endsWith('px') || trimmed.endsWith('rem') || trimmed.endsWith('em')) {
			return trimmed
		}
		const parsed = parseFloat(trimmed)
		if (!isNaN(parsed)) return `${parsed}px`
	}
	return '16px'
})
</script>

<template>
	<svg
		v-if="iconPath"
		xmlns="http://www.w3.org/2000/svg"
		:width="numericSize"
		:height="numericSize"
		:style="{
			width: numericSize,
			height: numericSize,
			maxWidth: numericSize,
			maxHeight: numericSize,
		}"
		viewBox="0 0 16 16"
		fill="none"
		:stroke="props.color"
		stroke-width="1.5"
		stroke-linecap="round"
		stroke-linejoin="round"
		class="pixel-icon"
		v-html="iconPath"
	/>
</template>

<style scoped>
.pixel-icon {
	display: inline-block;
	vertical-align: middle;
	flex-shrink: 0;
	shape-rendering: crispEdges;
	box-sizing: content-box;
}
</style>
