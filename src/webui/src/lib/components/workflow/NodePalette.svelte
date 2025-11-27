<!--
  Node Palette Component
  ragged WebUI v0.9.4

  Palette of available workflow nodes for drag and drop
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { NodeType, NodeCategory } from '$lib/workflow/types';
	import { NODE_COLOURS } from '$lib/workflow/types';
	import { getNodesByCategory, NODE_DEFINITIONS } from '$lib/workflow/nodes';

	export let searchQuery = '';

	const dispatch = createEventDispatcher<{
		nodeAdd: { type: NodeType; x: number; y: number };
	}>();

	const categories = getNodesByCategory();
	const categoryLabels: Record<NodeCategory, string> = {
		input: 'Input',
		processing: 'Processing',
		retrieval: 'Retrieval',
		output: 'Output',
		utility: 'Utility'
	};

	const categoryOrder: NodeCategory[] = ['input', 'processing', 'retrieval', 'output', 'utility'];

	$: filteredCategories = getFilteredCategories(searchQuery);

	function getFilteredCategories(query: string): Record<string, typeof categories[string]> {
		if (!query) return categories;

		const result: Record<string, typeof categories[string]> = {};
		const lowerQuery = query.toLowerCase();

		for (const [category, nodes] of Object.entries(categories)) {
			const filtered = nodes.filter(
				(node) =>
					node.label.toLowerCase().includes(lowerQuery) ||
					node.description.toLowerCase().includes(lowerQuery)
			);
			if (filtered.length > 0) {
				result[category] = filtered;
			}
		}

		return result;
	}

	function handleDragStart(event: DragEvent, type: NodeType) {
		if (event.dataTransfer) {
			event.dataTransfer.setData('application/workflow-node', type);
			event.dataTransfer.effectAllowed = 'copy';
		}
	}

	function handleNodeClick(type: NodeType) {
		// Add node at default position (will be centred on canvas)
		dispatch('nodeAdd', { type, x: 100, y: 100 });
	}
</script>

<div class="node-palette">
	<div class="node-palette__search">
		<svg
			width="16"
			height="16"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="2"
		>
			<circle cx="11" cy="11" r="8" />
			<line x1="21" y1="21" x2="16.65" y2="16.65" />
		</svg>
		<input
			type="search"
			placeholder="Search nodes..."
			bind:value={searchQuery}
			class="node-palette__input"
		/>
	</div>

	<div class="node-palette__categories">
		{#each categoryOrder as category}
			{#if filteredCategories[category]?.length > 0}
				<div class="node-palette__category">
					<h4
						class="node-palette__category-title"
						style="--category-colour: {NODE_COLOURS[category]}"
					>
						{categoryLabels[category]}
					</h4>

					<div class="node-palette__nodes">
						{#each filteredCategories[category] as node}
							<button
								type="button"
								class="node-palette__node"
								style="--node-colour: {node.colour}"
								draggable="true"
								on:dragstart={(e) => handleDragStart(e, node.type)}
								on:click={() => handleNodeClick(node.type)}
								title={node.description}
							>
								<span
									class="node-palette__node-indicator"
									style="background-color: {node.colour}"
								/>
								<span class="node-palette__node-label">{node.label}</span>
							</button>
						{/each}
					</div>
				</div>
			{/if}
		{/each}

		{#if Object.keys(filteredCategories).length === 0}
			<div class="node-palette__empty">
				<p>No nodes match your search</p>
			</div>
		{/if}
	</div>

	<div class="node-palette__help">
		<p>Drag nodes to canvas or click to add</p>
	</div>
</div>

<style>
	.node-palette {
		display: flex;
		flex-direction: column;
		width: 240px;
		height: 100%;
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
		overflow: hidden;
	}

	.node-palette__search {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-3);
		border-bottom: 1px solid var(--color-border-light);
		color: var(--color-text-muted);
	}

	.node-palette__input {
		flex: 1;
		padding: var(--space-2);
		font-size: var(--font-size-sm);
		color: var(--color-text-primary);
		background-color: var(--color-bg-secondary);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		outline: none;
	}

	.node-palette__input:focus {
		border-color: var(--color-primary);
	}

	.node-palette__categories {
		flex: 1;
		overflow-y: auto;
		padding: var(--space-2);
	}

	.node-palette__category {
		margin-bottom: var(--space-3);
	}

	.node-palette__category-title {
		margin: 0 0 var(--space-2);
		padding: var(--space-1) var(--space-2);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		border-left: 3px solid var(--category-colour);
		background-color: var(--color-bg-secondary);
		border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
	}

	.node-palette__nodes {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.node-palette__node {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-2);
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		text-align: left;
		background: none;
		border: 1px solid transparent;
		border-radius: var(--radius-md);
		cursor: grab;
		transition: all var(--transition-fast);
	}

	.node-palette__node:hover {
		background-color: var(--color-bg-secondary);
		border-color: var(--color-border-light);
		color: var(--color-text-primary);
	}

	.node-palette__node:active {
		cursor: grabbing;
	}

	.node-palette__node-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.node-palette__node-label {
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.node-palette__empty {
		padding: var(--space-4);
		text-align: center;
		color: var(--color-text-muted);
		font-size: var(--font-size-sm);
	}

	.node-palette__help {
		padding: var(--space-3);
		border-top: 1px solid var(--color-border-light);
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
		text-align: center;
	}
</style>
