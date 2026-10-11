<script setup lang="ts">
import { computed } from 'vue'

interface ColumnDef {
	key?: string
	name?: string
	label?: string
	title?: string
	sortable?: boolean
	width?: string
}

interface Props {
	items: any[]
	columns: (string | ColumnDef)[]
	striped?: boolean
	hoverable?: boolean
	perPage?: number
	currentPage?: number
}

const props = withDefaults(defineProps<Props>(), {
	striped: true,
	hoverable: true,
	perPage: 0,
	currentPage: 1,
})

interface NormalizedCol {
	key: string
	label: string
}

const normalizedColumns = computed<NormalizedCol[]>(() => {
	return props.columns.map((c) => {
		if (typeof c === 'string') {
			return { key: c, label: c }
		}
		const key = c.key || c.name || ''
		const label = c.label || c.title || key
		return { key, label }
	})
})

const paginatedItems = computed(() => {
	if (!props.perPage || props.perPage <= 0) {
		return props.items
	}
	const start = (props.currentPage - 1) * props.perPage
	return props.items.slice(start, start + props.perPage)
})
</script>

<template>
	<div class="pixel-table-wrapper">
		<table
			:class="[
				'pixel-table',
				{ 'pixel-table--striped': striped, 'pixel-table--hoverable': hoverable },
			]"
		>
			<thead>
				<tr>
					<th v-for="col in normalizedColumns" :key="col.key" class="pixel-th">
						{{ col.label }}
					</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(row, idx) in paginatedItems" :key="row.id || idx" class="pixel-tr">
					<td v-for="col in normalizedColumns" :key="col.key" class="pixel-td">
						<!-- Check dynamic slot name #cell(key) -->
						<slot
							:name="`cell(${col.key})`"
							:value="row[col.key]"
							:row-data="row"
							:row-index="idx"
						>
							{{ row[col.key] ?? '—' }}
						</slot>
					</td>
				</tr>
				<tr v-if="paginatedItems.length === 0">
					<td :colspan="normalizedColumns.length" class="pixel-empty-td">
						No records found
					</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<style scoped>
.pixel-table-wrapper {
	width: 100%;
	overflow-x: auto;
	border: 2px solid var(--pixel-border);
	box-shadow: 0 3px 0 0 rgba(0, 0, 0, 0.4);
	border-radius: 3px;
	background-color: var(--pixel-surface);
}

.pixel-table {
	width: 100%;
	border-collapse: collapse;
	text-align: left;
	font-family: var(--font-body);
	font-size: 13px;
}

.pixel-th {
	font-family: var(--font-pixel);
	font-size: 11px;
	text-transform: uppercase;
	letter-spacing: 0.05em;
	background-color: var(--pixel-surface-alt);
	color: var(--pixel-text-muted);
	padding: 10px 14px;
	border-bottom: 2px solid var(--pixel-border);
	font-weight: 500;
	white-space: nowrap;
}

.pixel-td {
	padding: 10px 14px;
	border-bottom: 1px solid var(--pixel-border);
	color: var(--pixel-text);
	vertical-align: middle;
}

.pixel-table--striped tbody tr:nth-child(even) {
	background-color: rgba(255, 255, 255, 0.02);
}

.pixel-table--hoverable tbody tr:hover {
	background-color: rgba(90, 50, 163, 0.12);
}

.pixel-empty-td {
	padding: 24px;
	text-align: center;
	color: var(--pixel-text-dim);
	font-family: var(--font-pixel);
}
</style>
