<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import PixelIcon from './PixelIcon.vue'

interface Props {
  modelValue?: Date | string | null
  label?: string
  placeholder?: string
  required?: boolean
  clearable?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  placeholder: 'DD/MM/YYYY',
  required: false,
  clearable: false,
  disabled: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: Date | null): void
}>()

const isOpen = ref(false)
const containerRef = ref<HTMLElement | null>(null)

// Parse modelValue into a safe local Date
const selectedDate = computed<Date | null>(() => {
  if (!props.modelValue) return null
  if (props.modelValue instanceof Date) {
    return isNaN(props.modelValue.getTime()) ? null : props.modelValue
  }
  if (typeof props.modelValue === 'string') {
    const s = props.modelValue.trim()
    if (!s) return null
    // YYYY-MM-DD
    const iso = s.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/)
    if (iso) {
      return new Date(Number(iso[1]), Number(iso[2]) - 1, Number(iso[3]))
    }
    // DD/MM/YYYY or DD-MM-YYYY
    const dmy = s.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})/)
    if (dmy) {
      return new Date(Number(dmy[3]), Number(dmy[2]) - 1, Number(dmy[1]))
    }
    const d = new Date(s)
    return isNaN(d.getTime()) ? null : d
  }
  return null
})

// Current month/year navigation state in the calendar popup
const viewYear = ref<number>(new Date().getFullYear())
const viewMonth = ref<number>(new Date().getMonth())

// Sync calendar view when popover opens or selected date changes
watch(
  () => props.modelValue,
  () => {
    if (selectedDate.value) {
      viewYear.value = selectedDate.value.getFullYear()
      viewMonth.value = selectedDate.value.getMonth()
    }
  },
  { immediate: true }
)

const MONTH_NAMES = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
]

const WEEKDAY_NAMES = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']

const monthYearTitle = computed(() => {
  return `${MONTH_NAMES[viewMonth.value]} ${viewYear.value}`
})

const formattedDisplay = computed(() => {
  if (!selectedDate.value) return ''
  const d = selectedDate.value
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = d.getFullYear()
  return `${day}/${month}/${year}`
})

interface CalendarDay {
  year: number
  month: number
  date: number
  isCurrentMonth: boolean
  isToday: boolean
  isSelected: boolean
}

const calendarDays = computed<CalendarDay[]>(() => {
  const y = viewYear.value
  const m = viewMonth.value

  const firstDay = new Date(y, m, 1)
  const firstDayOfWeek = firstDay.getDay() // 0 = Sunday
  const lastDay = new Date(y, m + 1, 0)
  const daysInCurrentMonth = lastDay.getDate()

  const today = new Date()
  const isTodayDate = (yr: number, mo: number, dt: number) => {
    return (
      today.getFullYear() === yr &&
      today.getMonth() === mo &&
      today.getDate() === dt
    )
  }

  const isSelectedDate = (yr: number, mo: number, dt: number) => {
    if (!selectedDate.value) return false
    return (
      selectedDate.value.getFullYear() === yr &&
      selectedDate.value.getMonth() === mo &&
      selectedDate.value.getDate() === dt
    )
  }

  const days: CalendarDay[] = []

  // Trailing days from previous month
  const prevMonthLastDay = new Date(y, m, 0).getDate()
  for (let i = firstDayOfWeek - 1; i >= 0; i--) {
    const dt = prevMonthLastDay - i
    const prevMo = m === 0 ? 11 : m - 1
    const prevYr = m === 0 ? y - 1 : y
    days.push({
      year: prevYr,
      month: prevMo,
      date: dt,
      isCurrentMonth: false,
      isToday: isTodayDate(prevYr, prevMo, dt),
      isSelected: isSelectedDate(prevYr, prevMo, dt),
    })
  }

  // Days of current month
  for (let dt = 1; dt <= daysInCurrentMonth; dt++) {
    days.push({
      year: y,
      month: m,
      date: dt,
      isCurrentMonth: true,
      isToday: isTodayDate(y, m, dt),
      isSelected: isSelectedDate(y, m, dt),
    })
  }

  // Next month days to fill complete grid rows (35 or 42 cells)
  const remainingInWeek = (7 - (days.length % 7)) % 7
  const minRows = days.length + remainingInWeek <= 35 ? 35 : 42
  const totalCellsNeeded = Math.max(days.length + remainingInWeek, minRows)
  const extraDays = totalCellsNeeded - days.length

  for (let dt = 1; dt <= extraDays; dt++) {
    const nextMo = m === 11 ? 0 : m + 1
    const nextYr = m === 11 ? y + 1 : y
    days.push({
      year: nextYr,
      month: nextMo,
      date: dt,
      isCurrentMonth: false,
      isToday: isTodayDate(nextYr, nextMo, dt),
      isSelected: isSelectedDate(nextYr, nextMo, dt),
    })
  }

  return days
})

const toggleOpen = () => {
  if (props.disabled) return
  if (!isOpen.value && selectedDate.value) {
    viewYear.value = selectedDate.value.getFullYear()
    viewMonth.value = selectedDate.value.getMonth()
  }
  isOpen.value = !isOpen.value
}

const prevMonth = () => {
  if (viewMonth.value === 0) {
    viewMonth.value = 11
    viewYear.value -= 1
  } else {
    viewMonth.value -= 1
  }
}

const nextMonth = () => {
  if (viewMonth.value === 11) {
    viewMonth.value = 0
    viewYear.value += 1
  } else {
    viewMonth.value += 1
  }
}

const selectDay = (day: CalendarDay) => {
  const chosen = new Date(day.year, day.month, day.date)
  emit('update:modelValue', chosen)
  isOpen.value = false
}

const selectToday = () => {
  const today = new Date()
  viewYear.value = today.getFullYear()
  viewMonth.value = today.getMonth()
  emit('update:modelValue', today)
  isOpen.value = false
}

const handleClear = (e?: Event) => {
  if (e) e.stopPropagation()
  emit('update:modelValue', null)
}

const dropdownRef = ref<HTMLElement | null>(null)
const dropdownStyle = ref<Record<string, string>>({})

const updateDropdownPosition = () => {
  if (!containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  const dropdownHeight = 310
  const spaceBelow = window.innerHeight - rect.bottom

  const leftPos = Math.max(8, Math.min(window.innerWidth - 290, rect.left))

  if (spaceBelow < dropdownHeight && rect.top > dropdownHeight) {
    dropdownStyle.value = {
      position: 'fixed',
      top: `${Math.max(8, rect.top - dropdownHeight - 6)}px`,
      left: `${leftPos}px`,
      width: '280px',
      zIndex: '9999',
    }
  } else {
    dropdownStyle.value = {
      position: 'fixed',
      top: `${rect.bottom + 6}px`,
      left: `${leftPos}px`,
      width: '280px',
      zIndex: '9999',
    }
  }
}

watch(isOpen, (open) => {
  if (open) {
    updateDropdownPosition()
    window.addEventListener('scroll', updateDropdownPosition, true)
    window.addEventListener('resize', updateDropdownPosition)
  } else {
    window.removeEventListener('scroll', updateDropdownPosition, true)
    window.removeEventListener('resize', updateDropdownPosition)
  }
})

const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as Node
  const inContainer = containerRef.value && containerRef.value.contains(target)
  const inDropdown = dropdownRef.value && dropdownRef.value.contains(target)
  if (!inContainer && !inDropdown) {
    isOpen.value = false
  }
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && isOpen.value) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('pointerdown', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('scroll', updateDropdownPosition, true)
  window.removeEventListener('resize', updateDropdownPosition)
})
</script>

<template>
  <div
    ref="containerRef"
    :class="['pixel-date-wrapper', { 'pixel-date--disabled': disabled }]"
  >
    <label v-if="label" class="pixel-date-label">
      {{ label }}
      <span v-if="required" class="required-star">*</span>
    </label>

    <div
      class="pixel-date-input-box"
      :class="{ 'is-active': isOpen }"
      @click="toggleOpen"
    >
      <input
        type="text"
        readonly
        :value="formattedDisplay"
        :placeholder="placeholder"
        :disabled="disabled"
        class="pixel-date-display"
        tabindex="0"
        @keydown.enter.prevent="toggleOpen"
        @keydown.space.prevent="toggleOpen"
      />

      <button
        v-if="clearable && selectedDate && !disabled"
        type="button"
        class="pixel-date-clear-btn"
        aria-label="Clear date"
        @click="handleClear"
      >
        <PixelIcon name="cross" :size="12" />
      </button>

      <div class="pixel-date-icon-btn">
        <PixelIcon name="calendar" :size="14" />
      </div>
    </div>

    <!-- CUSTOM PIXEL ART DROPDOWN CALENDAR (TELEPORTED OUTSIDE TO PREVENT MODAL CLIPPING) -->
    <Teleport to="body">
      <transition name="pixel-drop">
        <div
          v-if="isOpen"
          ref="dropdownRef"
          class="pixel-calendar-dropdown"
          :style="dropdownStyle"
          @click.stop
        >
          <!-- Calendar Header -->
          <div class="calendar-header">
            <button
              type="button"
              class="pixel-nav-btn"
              aria-label="Previous month"
              @click.stop="prevMonth"
            >
              <PixelIcon name="chevron_left" :size="12" />
            </button>

            <span class="calendar-title">{{ monthYearTitle }}</span>

            <button
              type="button"
              class="pixel-nav-btn"
              aria-label="Next month"
              @click.stop="nextMonth"
            >
              <PixelIcon name="chevron_right" :size="12" />
            </button>
          </div>

          <!-- Weekday Labels -->
          <div class="calendar-weekdays">
            <span
              v-for="dayName in WEEKDAY_NAMES"
              :key="dayName"
              class="calendar-weekday"
            >
              {{ dayName }}
            </span>
          </div>

          <!-- Days Grid -->
          <div class="calendar-grid">
            <button
              v-for="(day, idx) in calendarDays"
              :key="`${day.year}-${day.month}-${day.date}-${idx}`"
              type="button"
              class="calendar-day-btn"
              :class="{
                'is-current-month': day.isCurrentMonth,
                'is-other-month': !day.isCurrentMonth,
                'is-today': day.isToday,
                'is-selected': day.isSelected,
              }"
              @click.stop="selectDay(day)"
            >
              <span class="day-number">{{ day.date }}</span>
            </button>
          </div>

          <!-- Calendar Quick Action Footer -->
          <div class="calendar-footer">
            <button
              type="button"
              class="pixel-quick-btn"
              @click.stop="selectToday"
            >
              Today
            </button>
            <button
              v-if="clearable && selectedDate"
              type="button"
              class="pixel-quick-btn is-clear"
              @click.stop="handleClear"
            >
              Clear
            </button>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<style scoped>
.pixel-date-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}

.pixel-date-label {
  font-family: var(--font-pixel);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--pixel-text-muted);
}

.required-star {
  color: var(--pixel-btn-danger-bg);
}

.pixel-date-input-box {
  position: relative;
  display: flex;
  align-items: center;
  background-color: var(--pixel-bg-alt);
  border: 2px solid var(--pixel-border);
  box-shadow: inset 0 2px 0 0 rgba(0, 0, 0, 0.4);
  border-radius: 2px;
  padding: 0 8px;
  cursor: pointer;
  transition: border-color 0.1s ease, box-shadow 0.1s ease;
  user-select: none;
}

.pixel-date-input-box:hover {
  border-color: var(--pixel-border-bright);
}

.pixel-date-input-box.is-active {
  border-color: var(--pixel-btn-primary-hover);
  box-shadow: inset 0 2px 0 0 rgba(0, 0, 0, 0.4), 0 0 0 1px var(--pixel-btn-primary-border);
}

.pixel-date-display {
  width: 100%;
  background: transparent;
  border: none;
  outline: none;
  padding: 8px 4px;
  color: var(--pixel-text);
  font-family: var(--font-body);
  font-size: 13px;
  cursor: pointer;
}

.pixel-date-display::placeholder {
  color: var(--pixel-text-dim);
}

.pixel-date-clear-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--pixel-text-dim);
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.1s ease;
}

.pixel-date-clear-btn:hover {
  color: var(--pixel-btn-danger-bg);
}

.pixel-date-icon-btn {
  display: flex;
  align-items: center;
  color: var(--pixel-text-muted);
  pointer-events: none;
  padding-left: 4px;
}

/* CUSTOM POPUP CALENDAR */
.pixel-calendar-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 1000;
  width: 280px;
  background: var(--pixel-surface);
  border: 2px solid var(--pixel-border);
  box-shadow:
    0 5px 0 0 var(--pixel-border-dark),
    0 8px 24px rgba(0, 0, 0, 0.6);
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  user-select: none;
}

/* Header */
.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 6px;
  border-bottom: 2px solid var(--pixel-border);
}

.calendar-title {
  font-family: var(--font-pixel);
  font-size: 13px;
  font-weight: 700;
  color: var(--pixel-text);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.pixel-nav-btn {
  background: var(--pixel-btn-secondary-bg);
  border: 1px solid var(--pixel-btn-secondary-border);
  box-shadow: 0 2px 0 0 var(--pixel-btn-secondary-shade);
  color: var(--pixel-text);
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.05s ease, box-shadow 0.05s ease;
}

.pixel-nav-btn:hover {
  background: var(--pixel-btn-secondary-hover);
}

.pixel-nav-btn:active {
  transform: translateY(2px);
  box-shadow: 0 0 0 0 var(--pixel-btn-secondary-shade);
}

/* Weekdays */
.calendar-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  text-align: center;
}

.calendar-weekday {
  font-family: var(--font-pixel);
  font-size: 10px;
  color: var(--pixel-text-dim);
  text-transform: uppercase;
  padding: 2px 0;
}

/* Grid */
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.calendar-day-btn {
  height: 30px;
  background: var(--pixel-bg-alt);
  border: 1px solid transparent;
  color: var(--pixel-text);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
  position: relative;
  transition: background-color 0.1s ease, border-color 0.1s ease;
}

.calendar-day-btn:hover {
  background: var(--pixel-surface-raised);
  border-color: var(--pixel-border-bright);
}

.day-number {
  font-family: var(--font-pixel);
  font-size: 11px;
}

.calendar-day-btn.is-other-month {
  color: var(--pixel-text-dim);
  opacity: 0.4;
  background: transparent;
}

.calendar-day-btn.is-today {
  border: 1px dashed var(--gold-glow);
  color: var(--gold-glow);
}

.calendar-day-btn.is-selected {
  background: var(--pixel-btn-primary-bg) !important;
  border: 1px solid var(--pixel-btn-primary-border) !important;
  box-shadow: inset 0 -2px 0 0 var(--pixel-btn-primary-shade);
  color: #ffffff !important;
  font-weight: 700;
}

.calendar-day-btn:active {
  transform: translateY(1px);
}

/* Footer */
.calendar-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 6px;
  border-top: 2px solid var(--pixel-border);
}

.pixel-quick-btn {
  background: transparent;
  border: 1px solid var(--pixel-border);
  box-shadow: 0 2px 0 0 var(--pixel-border-dark);
  color: var(--pixel-text-muted);
  font-family: var(--font-pixel);
  font-size: 10px;
  text-transform: uppercase;
  padding: 3px 8px;
  cursor: pointer;
  transition: all 0.1s ease;
}

.pixel-quick-btn:hover {
  background: var(--pixel-surface-raised);
  color: var(--pixel-text);
}

.pixel-quick-btn:active {
  transform: translateY(2px);
  box-shadow: 0 0 0 0 var(--pixel-border-dark);
}

.pixel-quick-btn.is-clear:hover {
  color: var(--pixel-btn-danger-bg);
  border-color: var(--pixel-btn-danger-border);
}

/* Transitions */
.pixel-drop-enter-active,
.pixel-drop-leave-active {
  transition: opacity 0.12s ease, transform 0.12s ease;
}

.pixel-drop-enter-from,
.pixel-drop-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.pixel-date--disabled {
  opacity: 0.5;
  pointer-events: none;
}
</style>
