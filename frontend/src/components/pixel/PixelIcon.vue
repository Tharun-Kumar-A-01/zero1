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

// Normalization alias dictionary
const ALIAS_MAP: Record<string, string> = {
  trash: 'Bin',
  bin: 'Bin',
  delete: 'Bin',
  remove: 'Bin',
  check: 'Tick',
  tick: 'Tick',
  done: 'Tick',
  success: 'Tick',
  close: 'Cross',
  cross: 'Cross',
  x: 'Cross',
  cancel: 'Cross',
  plus: 'Plus',
  add: 'Plus',
  minus: 'Minus',
  search: 'Search',
  edit: 'Edit',
  pencil: 'Edit',
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
  warning: 'Alert',
  alert: 'Alert',
  user: 'Person',
  person: 'Person',
  users: 'People',
  people: 'People',
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
  calendar: 'Calendar',
  calendar_today: 'Calendar',
  date_range: 'Calendar',
  event: 'Calendar',
  event_busy: 'Calendar',
  beach_access: 'TreeFir',
  school: 'GraduateCap',
  filter: 'Filter',
  sort: 'Sort',
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
  external: 'ExternalLink',
  'external-link': 'ExternalLink',
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
}

const charmMap = charm as unknown as Record<string, { paths: string }>

const iconPath = computed(() => {
  const raw = props.name.trim()
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

  // Fallback to Star or Circle
  return charmMap['Star']?.paths || ''
})

const numericSize = computed(() => {
  if (typeof props.size === 'number') return `${props.size}px`
  return props.size
})
</script>

<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    :width="numericSize"
    :height="numericSize"
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
}
</style>
