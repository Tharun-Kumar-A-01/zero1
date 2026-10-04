/**
 * Date formatting utilities for Indian dd/mm/yyyy format.
 */

export function formatIndianDate(value: Date | string | null | undefined): string {
	if (!value) return '—'
	const d = typeof value === 'string' ? new Date(value) : value
	if (isNaN(d.getTime())) return String(value)

	const day = String(d.getDate()).padStart(2, '0')
	const month = String(d.getMonth() + 1).padStart(2, '0')
	const year = d.getFullYear()
	return `${day}/${month}/${year}`
}

export function formatISODate(value: Date | string | null | undefined): string {
	if (!value) return ''
	const d = typeof value === 'string' ? new Date(value) : value
	if (isNaN(d.getTime())) return ''

	const year = d.getFullYear()
	const month = String(d.getMonth() + 1).padStart(2, '0')
	const day = String(d.getDate()).padStart(2, '0')
	return `${year}-${month}-${day}`
}

export function formatDateRange(value: unknown): string {
	if (!value) return ''
	if (typeof value === 'object' && value !== null && 'start' in value) {
		const range = value as { start?: Date | string | null; end?: Date | string | null }
		if (range.start && range.end) {
			return `${formatIndianDate(range.start)} – ${formatIndianDate(range.end)}`
		}
		if (range.start) {
			return formatIndianDate(range.start)
		}
	}
	if (value instanceof Date || typeof value === 'string') {
		return formatIndianDate(value)
	}
	return ''
}

