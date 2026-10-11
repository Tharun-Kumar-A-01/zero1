<script setup lang="ts">
import { computed } from 'vue'

import flameImg from '@/assets/pixel-icons/flame.png'
import crownImg from '@/assets/pixel-icons/crown.png'
import trophyImg from '@/assets/pixel-icons/trophy.png'
import silverImg from '@/assets/pixel-icons/silver.png'
import bronzeImg from '@/assets/pixel-icons/bronze.png'
import starImg from '@/assets/pixel-icons/star.png'
import swordImg from '@/assets/pixel-icons/icons_8x8/sword_thick.png'
import shieldImg from '@/assets/pixel-icons/icons_8x8/shield.png'
import gemImg from '@/assets/pixel-icons/gem.png'
import potionImg from '@/assets/pixel-icons/potion.png'
import chestImg from '@/assets/pixel-icons/icons_8x8/iron_chest_open.png'
import scrollImg from '@/assets/pixel-icons/scroll.png'
import starGoldImg from '@/assets/pixel-icons/star_gold.png'
import starSilverImg from '@/assets/pixel-icons/star_silver.png'
import starBronzeImg from '@/assets/pixel-icons/star_bronze.png'
import thunderImg from '@/assets/pixel-icons/thunder.png'
import gemAmberImg from '@/assets/pixel-icons/gem_amber.png'
import gemRubyImg from '@/assets/pixel-icons/gem_ruby.png'
import gemSapphireImg from '@/assets/pixel-icons/gem_sapphire.png'
import gemDiamondImg from '@/assets/pixel-icons/gem_diamond.png'
import gemEmeraldImg from '@/assets/pixel-icons/gem_emerald.png'

interface Props {
	name?: string
	scale?: number
	size?: number
}

const props = withDefaults(defineProps<Props>(), {
	name: 'flame',
	scale: 1,
})

// 8x8 icons and faces glob
const icons8x8Modules = import.meta.glob<{ default: string }>(
	['@/assets/pixel-icons/icons_8x8/*.png', '@/assets/pixel-icons/icons_8x8/faces/*.png'],
	{ eager: true },
)
const ICONS_8X8_MAP: Record<string, string> = {}
for (const [path, module] of Object.entries(icons8x8Modules)) {
	const filename = path.split('/').pop()?.replace('.png', '').toLowerCase()
	if (filename) {
		ICONS_8X8_MAP[filename] = module.default
	}
}

// RPG Maker icons glob for seamless icon lookups
const rpgMakerModules = import.meta.glob<{ default: string }>(
	'@/assets/pixel-icons/rpg-maker/*.png',
	{
		eager: true,
	},
)
const RPG_MAKER_MAP: Record<string, string> = {}
for (const [path, module] of Object.entries(rpgMakerModules)) {
	const filename = path.split('/').pop()?.replace('.png', '').toLowerCase()
	if (filename) {
		RPG_MAKER_MAP[filename] = module.default
	}
}

const ASSET_MAP: Record<string, string> = {
	flame: flameImg,
	fire: flameImg,
	ember: flameImg,
	streak: flameImg,
	crown: crownImg,
	trophy: trophyImg,
	gold: starGoldImg,
	star_gold: starGoldImg,
	rank1: starGoldImg,
	silver: starSilverImg,
	star_silver: starSilverImg,
	rank2: starSilverImg,
	bronze: starBronzeImg,
	star_bronze: starBronzeImg,
	rank3: starBronzeImg,
	star: starGoldImg,
	thunder: thunderImg,
	lightning: thunderImg,
	exp: thunderImg,
	xp: thunderImg,
	bolt: thunderImg,
	sword: swordImg,
	swords: swordImg,
	blade: swordImg,
	dagger: swordImg,
	sword_thick: swordImg,
	shield: shieldImg,
	gem: gemRubyImg,
	ruby: gemRubyImg,
	gem_ruby: gemRubyImg,
	amber: gemAmberImg,
	gem_amber: gemAmberImg,
	topaz: gemAmberImg,
	sapphire: gemSapphireImg,
	gem_sapphire: gemSapphireImg,
	diamond: gemDiamondImg,
	gem_diamond: gemDiamondImg,
	pearl: gemDiamondImg,
	emerald: gemEmeraldImg,
	gem_emerald: gemEmeraldImg,
	chest: chestImg,
	iron_chest_open: chestImg,
	potion: potionImg,
	key: chestImg,
	book: scrollImg,
	scroll: scrollImg,
	tome: scrollImg,
}

const src = computed(() => {
	const key = (props.name || 'flame').toLowerCase().trim()
	return ASSET_MAP[key] ?? ICONS_8X8_MAP[key] ?? RPG_MAKER_MAP[key] ?? null
})

const pixelDimension = computed(() => {
	if (props.size) return props.size
	return Math.round(16 * props.scale)
})
</script>

<template>
	<img
		v-if="src"
		:src="src"
		:alt="props.name || 'pixel icon'"
		:width="pixelDimension"
		:height="pixelDimension"
		:style="{
			width: `${pixelDimension}px`,
			height: `${pixelDimension}px`,
			maxWidth: `${pixelDimension}px`,
			maxHeight: `${pixelDimension}px`,
		}"
		class="pixel-sprite"
		draggable="false"
	/>
</template>

<style scoped>
.pixel-sprite {
	display: inline-block;
	vertical-align: middle;
	image-rendering: pixelated;
	image-rendering: crisp-edges;
	object-fit: contain;
	flex-shrink: 0;
	user-select: none;
}
</style>
