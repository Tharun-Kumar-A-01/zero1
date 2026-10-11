const faceModules = import.meta.glob<{ default: string }>(
	'@/assets/pixel-icons/icons_8x8/faces/*.png',
	{ eager: true },
)

export interface FaceItem {
	id: string
	name: string
	url: string
}

export const FACE_MAP: Record<string, string> = {}
export const AVAILABLE_FACES: FaceItem[] = []

for (const [path, mod] of Object.entries(faceModules)) {
	const filename = path
		.split('/')
		.pop()
		?.replace(/\.png$/i, '')
		.toLowerCase()
	if (filename) {
		FACE_MAP[filename] = mod.default
		AVAILABLE_FACES.push({
			id: filename,
			name: filename.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
			url: mod.default,
		})
	}
}

// Sort alphabetically by human-readable name
AVAILABLE_FACES.sort((a, b) => a.name.localeCompare(b.name))

export function getAvatarUrl(avatarId?: string | null): string | null {
	if (!avatarId) return null
	const key = avatarId.toLowerCase().trim()
	return FACE_MAP[key] ?? null
}
