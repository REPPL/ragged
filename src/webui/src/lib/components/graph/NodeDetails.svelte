<!--
  Node Details Component
  ragged WebUI v0.9.3

  Details panel for selected graph node
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { GraphNode, GraphEdge, NodeType } from '$lib/graph/types';
	import { NODE_COLOURS } from '$lib/graph/types';
	import Button from '../Button.svelte';

	export let node: GraphNode | null = null;
	export let connectedEdges: GraphEdge[] = [];

	const dispatch = createEventDispatcher<{
		close: void;
		navigate: { nodeId: string };
	}>();

	function getNodeTypeLabel(type: NodeType): string {
		const labels: Record<NodeType, string> = {
			document: 'Document',
			chunk: 'Chunk',
			entity: 'Entity',
			concept: 'Concept',
			topic: 'Topic'
		};
		return labels[type] || type;
	}

	function getConnectedNodes(edges: GraphEdge[], nodeId: string): { id: string; label: string; direction: 'in' | 'out' }[] {
		const result: { id: string; label: string; direction: 'in' | 'out' }[] = [];

		edges.forEach((edge) => {
			const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
			const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;
			const sourceLabel = typeof edge.source === 'string' ? edge.source : edge.source.label;
			const targetLabel = typeof edge.target === 'string' ? edge.target : edge.target.label;

			if (sourceId === nodeId) {
				result.push({ id: targetId, label: targetLabel, direction: 'out' });
			} else if (targetId === nodeId) {
				result.push({ id: sourceId, label: sourceLabel, direction: 'in' });
			}
		});

		return result;
	}

	$: connections = node ? getConnectedNodes(connectedEdges, node.id) : [];
</script>

<aside class="node-details" class:node-details--open={node !== null}>
	{#if node}
		<div class="node-details__header">
			<div class="node-details__title-row">
				<span
					class="node-details__type-badge"
					style="background-color: {NODE_COLOURS[node.type]}"
				>
					{getNodeTypeLabel(node.type)}
				</span>
			</div>
			<button
				type="button"
				class="node-details__close"
				on:click={() => dispatch('close')}
				aria-label="Close details"
			>
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="18" y1="6" x2="6" y2="18" />
					<line x1="6" y1="6" x2="18" y2="18" />
				</svg>
			</button>
		</div>

		<div class="node-details__content">
			<h2 class="node-details__label">{node.label}</h2>

			<section class="node-details__section">
				<h3 class="node-details__section-title">Properties</h3>
				<dl class="node-details__properties">
					<div class="node-details__property">
						<dt>ID</dt>
						<dd class="node-details__mono">{node.id}</dd>
					</div>
					<div class="node-details__property">
						<dt>Type</dt>
						<dd>{getNodeTypeLabel(node.type)}</dd>
					</div>
					{#if node.metadata}
						{#each Object.entries(node.metadata) as [key, value]}
							<div class="node-details__property">
								<dt>{key}</dt>
								<dd>{typeof value === 'object' ? JSON.stringify(value) : value}</dd>
							</div>
						{/each}
					{/if}
				</dl>
			</section>

			{#if connections.length > 0}
				<section class="node-details__section">
					<h3 class="node-details__section-title">
						Connections ({connections.length})
					</h3>
					<ul class="node-details__connections">
						{#each connections as conn}
							<li class="node-details__connection">
								<button
									type="button"
									class="node-details__connection-link"
									on:click={() => dispatch('navigate', { nodeId: conn.id })}
								>
									<span class="node-details__connection-direction">
										{conn.direction === 'in' ? '←' : '→'}
									</span>
									<span class="node-details__connection-label">{conn.label}</span>
								</button>
							</li>
						{/each}
					</ul>
				</section>
			{/if}
		</div>
	{:else}
		<div class="node-details__empty">
			<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
				<circle cx="12" cy="12" r="10" />
				<path d="M12 16v-4M12 8h.01" />
			</svg>
			<p>Click a node to view details</p>
		</div>
	{/if}
</aside>

<style>
	.node-details {
		display: flex;
		flex-direction: column;
		width: 300px;
		min-width: 300px;
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
		overflow: hidden;
	}

	.node-details__header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: var(--space-3);
		padding: var(--space-4);
		border-bottom: 1px solid var(--color-border-light);
		background-color: var(--color-bg-secondary);
	}

	.node-details__title-row {
		display: flex;
		align-items: center;
		gap: var(--space-2);
	}

	.node-details__type-badge {
		padding: var(--space-1) var(--space-2);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		color: white;
		border-radius: var(--radius-full);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.node-details__close {
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		padding: var(--space-1);
		color: var(--color-text-muted);
		background: none;
		border: none;
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.node-details__close:hover {
		color: var(--color-text-primary);
		background-color: var(--color-bg-tertiary);
	}

	.node-details__content {
		flex: 1;
		overflow-y: auto;
		padding: var(--space-4);
	}

	.node-details__label {
		margin: 0 0 var(--space-4);
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
		word-break: break-word;
	}

	.node-details__section {
		margin-bottom: var(--space-5);
	}

	.node-details__section:last-child {
		margin-bottom: 0;
	}

	.node-details__section-title {
		margin: 0 0 var(--space-3);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.node-details__properties {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
		margin: 0;
	}

	.node-details__property {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.node-details__property dt {
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.node-details__property dd {
		margin: 0;
		font-size: var(--font-size-sm);
		color: var(--color-text-primary);
		word-break: break-word;
	}

	.node-details__mono {
		font-family: var(--font-mono);
		font-size: var(--font-size-xs);
	}

	.node-details__connections {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.node-details__connection-link {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		width: 100%;
		padding: var(--space-2);
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		text-align: left;
		background: none;
		border: none;
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.node-details__connection-link:hover {
		background-color: var(--color-bg-secondary);
		color: var(--color-primary);
	}

	.node-details__connection-direction {
		flex-shrink: 0;
		width: 20px;
		text-align: center;
		color: var(--color-text-muted);
	}

	.node-details__connection-label {
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.node-details__empty {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--space-4);
		padding: var(--space-8);
		text-align: center;
		color: var(--color-text-muted);
	}

	.node-details__empty svg {
		opacity: 0.5;
	}
</style>
