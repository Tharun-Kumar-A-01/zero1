/**
 * Text and UI helper utilities for safe display and badge formatting.
 */

export function decodeHtmlEntities(text: string | null | undefined): string {
	if (!text) return ''
	return text
		.replace(/&amp;/g, '&')
		.replace(/&lt;/g, '<')
		.replace(/&gt;/g, '>')
		.replace(/&quot;/g, '"')
		.replace(/&#039;/g, "'")
		.replace(/&le;/g, '<=')
		.replace(/&ge;/g, '>=')
}

export function formatDuration(totalSeconds: number | null | undefined): string {
	if (totalSeconds === null || totalSeconds === undefined || totalSeconds < 0) {
		return '00:00'
	}
	const hrs = Math.floor(totalSeconds / 3600)
	const mins = Math.floor((totalSeconds % 3600) / 60)
	const secs = totalSeconds % 60

	if (hrs > 0) {
		return `${hrs}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
	}
	return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

export function formatDurationHuman(totalSeconds: number | null | undefined): string {
	if (totalSeconds === null || totalSeconds === undefined || totalSeconds <= 0) {
		return '0s'
	}
	const mins = Math.floor(totalSeconds / 60)
	const secs = totalSeconds % 60
	if (mins > 0) {
		return `${mins}m ${secs}s`
	}
	return `${secs}s`
}

export function getDifficultyColor(
	difficulty: string | null | undefined
): 'success' | 'warning' | 'danger' | 'secondary' {
	const d = String(difficulty || '').toLowerCase().trim()
	if (d === 'easy') return 'success'
	if (d === 'medium') return 'warning'
	if (d === 'hard') return 'danger'
	return 'secondary'
}
