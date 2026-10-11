import { config } from '@vue/test-utils'
import * as pixelComponents from '@/components/pixel'

// Register all Pixel components globally for test-utils
for (const [name, component] of Object.entries(pixelComponents)) {
	config.global.components[name] = component
}
