<script setup lang="ts">
withDefaults(
	defineProps<{
		points: number | string
		size?: 'small' | 'medium' | 'large'
		showLabel?: boolean
	}>(),
	{
		size: 'medium',
		showLabel: true,
	}
)
</script>

<template>
	<span class="xp-stat" :class="`size-${size}`">
		<VaIcon name="star" class="xp-star-icon" />
		<span class="xp-val">{{ points }}</span>
		<span v-if="showLabel" class="xp-unit">XP</span>
	</span>
</template>

<style scoped>
.xp-stat {
	display: inline-flex;
	align-items: center;
	gap: 0.2rem;
	font-weight: 700;
	color: var(--va-text-primary);
	line-height: 1;
	vertical-align: middle;
}

/* SIZES */
.size-small {
	font-size: 0.78rem;
}
.size-small .xp-star-icon {
	font-size: 14px !important;
}

.size-medium {
	font-size: 0.9rem;
}
.size-medium .xp-star-icon {
	font-size: 16px !important;
}

.size-large {
	font-size: 1.1rem;
}
.size-large .xp-star-icon {
	font-size: 20px !important;
}

.xp-star-icon {
	color: var(--va-warning);
	flex-shrink: 0;
}

.xp-unit {
	font-size: 0.85em;
	opacity: 0.7;
	text-transform: uppercase;
	letter-spacing: 0.04em;
}
</style>
