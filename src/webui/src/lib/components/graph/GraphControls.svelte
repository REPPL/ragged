<!--
  Graph Controls Component
  ragged WebUI v0.9.3

  Controls for graph layout, zoom, and filtering
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { GraphLayout, GraphFilters, NodeType, EdgeType } from '$lib/graph/types';
	import { NODE_COLOURS, EDGE_COLOURS } from '$lib/graph/types';
	import Button from '../Button.svelte';

	export let layout: GraphLayout = { type: 'force' };
	export let filters: GraphFilters = {
		nodeTypes: ['document', 'chunk', 'entity', 'concept', 'topic'],
		edgeTypes: ['contains', 'references', 'similar', 'related', 'parent'],
		minWeight: 0,
		searchQuery: ''
	};
	export let zoom = 1;

	const dispatch = createEventDispatcher<{
		layoutChange: GraphLayout;
		filterChange: GraphFilters;
		zoomIn: void;
		zoomOut: void;
		fitView: void;
		reset: void;
		export: { format: 'png' | 'svg' };
	}>();

	const layoutOptions: { value: GraphLayout['type']; label: string }[] = [
		{ value: 'force', label: 'Force-directed' },
		{ value: 'radial', label: 'Radial' },
		{ value: 'hierarchical', label: 'Hierarchical' }
	];

	const nodeTypeOptions: { value: NodeType; label: string; colour: string }[] = [
		{ value: 'document', label: 'Documents', colour: NODE_COLOURS.document },
		{ value: 'chunk', label: 'Chunks', colour: NODE_COLOURS.chunk },
		{ value: 'entity', label: 'Entities', colour: NODE_COLOURS.entity },
		{ value: 'concept', label: 'Concepts', colour: NODE_COLOURS.concept },
		{ value: 'topic', label: 'Topics', colour: NODE_COLOURS.topic }
	];

	const edgeTypeOptions: { value: EdgeType; label: string; colour: string }[] = [
		{ value: 'contains', label: 'Contains', colour: EDGE_COLOURS.contains },
		{ value: 'references', label: 'References', colour: EDGE_COLOURS.references },
		{ value: 'similar', label: 'Similar', colour: EDGE_COLOURS.similar },
		{ value: 'related', label: 'Related', colour: EDGE_COLOURS.related },
		{ value: 'parent', label: 'Parent', colour: EDGE_COLOURS.parent }
	];

	function handleLayoutChange(type: GraphLayout['type']) {
		layout = { ...layout, type };
		dispatch('layoutChange', layout);
	}

	function toggleNodeType(type: NodeType) {
		const newTypes = filters.nodeTypes.includes(type)
			? filters.nodeTypes.filter((t) => t !== type)
			: [...filters.nodeTypes, type];

		filters = { ...filters, nodeTypes: newTypes };
		dispatch('filterChange', filters);
	}

	function toggleEdgeType(type: EdgeType) {
		const newTypes = filters.edgeTypes.includes(type)
			? filters.edgeTypes.filter((t) => t !== type)
			: [...filters.edgeTypes, type];

		filters = { ...filters, edgeTypes: newTypes };
		dispatch('filterChange', filters);
	}

	function handleSearch(event: Event) {
		const target = event.target as HTMLInputElement;
		filters = { ...filters, searchQuery: target.value };
		dispatch('filterChange', filters);
	}

	$: zoomPercentage = Math.round(zoom * 100);
</script>

<div class="graph-controls">
	<!-- Zoom controls -->
	<div class="graph-controls__section">
		<div class="graph-controls__zoom">
			<button
				type="button"
				class="graph-controls__zoom-btn"
				on:click={() => dispatch('zoomOut')}
				aria-label="Zoom out"
			>
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<circle cx="11" cy="11" r="8" />
					<line x1="21" y1="21" x2="16.65" y2="16.65" />
					<line x1="8" y1="11" x2="14" y2="11" />
				</svg>
			</button>
			<span class="graph-controls__zoom-level">{zoomPercentage}%</span>
			<button
				type="button"
				class="graph-controls__zoom-btn"
				on:click={() => dispatch('zoomIn')}
				aria-label="Zoom in"
			>
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<circle cx="11" cy="11" r="8" />
					<line x1="21" y1="21" x2="16.65" y2="16.65" />
					<line x1="11" y1="8" x2="11" y2="14" />
					<line x1="8" y1="11" x2="14" y2="11" />
				</svg>
			</button>
		</div>

		<div class="graph-controls__buttons">
			<button
				type="button"
				class="graph-controls__btn"
				on:click={() => dispatch('fitView')}
				title="Fit to view"
			>
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3" />
				</svg>
			</button>
			<button
				type="button"
				class="graph-controls__btn"
				on:click={() => dispatch('reset')}
				title="Reset view"
			>
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="1 4 1 10 7 10" />
					<polyline points="23 20 23 14 17 14" />
					<path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" />
				</svg>
			</button>
		</div>
	</div>

	<!-- Layout selector -->
	<div class="graph-controls__section">
		<h4 class="graph-controls__label">Layout</h4>
		<div class="graph-controls__layout-options">
			{#each layoutOptions as option}
				<button
					type="button"
					class="graph-controls__layout-btn"
					class:graph-controls__layout-btn--active={layout.type === option.value}
					on:click={() => handleLayoutChange(option.value)}
				>
					{option.label}
				</button>
			{/each}
		</div>
	</div>

	<!-- Node type filters -->
	<div class="graph-controls__section">
		<h4 class="graph-controls__label">Node Types</h4>
		<div class="graph-controls__filters">
			{#each nodeTypeOptions as option}
				<label class="graph-controls__filter">
					<input
						type="checkbox"
						checked={filters.nodeTypes.includes(option.value)}
						on:change={() => toggleNodeType(option.value)}
					/>
					<span
						class="graph-controls__filter-dot"
						style="background-color: {option.colour}"
					/>
					<span>{option.label}</span>
				</label>
			{/each}
		</div>
	</div>

	<!-- Edge type filters -->
	<div class="graph-controls__section">
		<h4 class="graph-controls__label">Edge Types</h4>
		<div class="graph-controls__filters">
			{#each edgeTypeOptions as option}
				<label class="graph-controls__filter">
					<input
						type="checkbox"
						checked={filters.edgeTypes.includes(option.value)}
						on:change={() => toggleEdgeType(option.value)}
					/>
					<span
						class="graph-controls__filter-line"
						style="background-color: {option.colour}"
					/>
					<span>{option.label}</span>
				</label>
			{/each}
		</div>
	</div>

	<!-- Export -->
	<div class="graph-controls__section">
		<h4 class="graph-controls__label">Export</h4>
		<div class="graph-controls__export">
			<Button variant="ghost" size="sm" on:click={() => dispatch('export', { format: 'png' })}>
				PNG
			</Button>
			<Button variant="ghost" size="sm" on:click={() => dispatch('export', { format: 'svg' })}>
				SVG
			</Button>
		</div>
	</div>
</div>

<style>
	.graph-controls {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
		width: 220px;
		padding: var(--space-4);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
	}

	.graph-controls__section {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	.graph-controls__label {
		margin: 0;
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.graph-controls__zoom {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-2);
	}

	.graph-controls__zoom-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		padding: 0;
		color: var(--color-text-secondary);
		background: none;
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.graph-controls__zoom-btn:hover {
		color: var(--color-text-primary);
		border-color: var(--color-border);
		background-color: var(--color-bg-secondary);
	}

	.graph-controls__zoom-level {
		min-width: 48px;
		text-align: center;
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-secondary);
	}

	.graph-controls__buttons {
		display: flex;
		justify-content: center;
		gap: var(--space-2);
	}

	.graph-controls__btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		padding: 0;
		color: var(--color-text-secondary);
		background: none;
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.graph-controls__btn:hover {
		color: var(--color-text-primary);
		border-color: var(--color-border);
		background-color: var(--color-bg-secondary);
	}

	.graph-controls__layout-options {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.graph-controls__layout-btn {
		padding: var(--space-2);
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		text-align: left;
		background: none;
		border: 1px solid transparent;
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.graph-controls__layout-btn:hover {
		background-color: var(--color-bg-secondary);
	}

	.graph-controls__layout-btn--active {
		background-color: var(--color-primary-light);
		color: var(--color-primary);
		border-color: var(--color-primary);
	}

	.graph-controls__filters {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.graph-controls__filter {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-1) 0;
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		cursor: pointer;
	}

	.graph-controls__filter input {
		margin: 0;
		width: 16px;
		height: 16px;
		accent-color: var(--color-primary);
	}

	.graph-controls__filter-dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
	}

	.graph-controls__filter-line {
		width: 16px;
		height: 3px;
		border-radius: 2px;
	}

	.graph-controls__export {
		display: flex;
		gap: var(--space-2);
	}
</style>
