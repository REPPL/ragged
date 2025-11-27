<!--
  Knowledge Graph Page
  ragged WebUI v0.9.3

  Interactive knowledge graph visualisation
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import type { GraphData, GraphLayout, GraphFilters, GraphNode, GraphEdge } from '$lib/graph/types';
	import { GraphView, GraphControls, NodeDetails } from '$lib/components/graph';
	import Button from '$lib/components/Button.svelte';
	import Skeleton from '$lib/components/Skeleton.svelte';
	import { addToast } from '$stores';

	let graphData: GraphData = { nodes: [], edges: [] };
	let layout: GraphLayout = { type: 'force' };
	let filters: GraphFilters = {
		nodeTypes: ['document', 'chunk', 'entity', 'concept', 'topic'],
		edgeTypes: ['contains', 'references', 'similar', 'related', 'parent'],
		minWeight: 0,
		searchQuery: ''
	};

	let selectedNode: GraphNode | null = null;
	let connectedEdges: GraphEdge[] = [];
	let hoveredNode: GraphNode | null = null;

	let loading = true;
	let error: string | null = null;
	let zoom = 1;

	let graphViewRef: GraphView;

	// Filter graph data based on current filters
	$: filteredData = filterGraphData(graphData, filters);

	function filterGraphData(data: GraphData, filters: GraphFilters): GraphData {
		// Filter nodes by type
		const filteredNodes = data.nodes.filter((node) => {
			if (!filters.nodeTypes.includes(node.type)) return false;
			if (filters.searchQuery) {
				const query = filters.searchQuery.toLowerCase();
				return node.label.toLowerCase().includes(query) || node.id.toLowerCase().includes(query);
			}
			return true;
		});

		const nodeIds = new Set(filteredNodes.map((n) => n.id));

		// Filter edges by type and ensure both nodes exist
		const filteredEdges = data.edges.filter((edge) => {
			if (!filters.edgeTypes.includes(edge.type)) return false;
			if (filters.minWeight && (edge.weight || 0) < filters.minWeight) return false;

			const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
			const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;

			return nodeIds.has(sourceId) && nodeIds.has(targetId);
		});

		return { nodes: filteredNodes, edges: filteredEdges };
	}

	async function loadGraphData() {
		loading = true;
		error = null;
		try {
			// TODO: Replace with actual API call
			// const data = await api.graph.getData();
			// graphData = data;

			// Mock data for demonstration
			graphData = generateMockGraphData();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load graph data';
			addToast({
				type: 'error',
				title: 'Failed to load graph',
				message: error
			});
		} finally {
			loading = false;
		}
	}

	function generateMockGraphData(): GraphData {
		const nodes: GraphNode[] = [
			// Documents
			{ id: 'doc-1', label: 'Technical Architecture', type: 'document' },
			{ id: 'doc-2', label: 'User Guide', type: 'document' },
			{ id: 'doc-3', label: 'API Reference', type: 'document' },

			// Chunks
			{ id: 'chunk-1', label: 'Introduction', type: 'chunk', metadata: { source: 'doc-1' } },
			{ id: 'chunk-2', label: 'System Overview', type: 'chunk', metadata: { source: 'doc-1' } },
			{ id: 'chunk-3', label: 'Getting Started', type: 'chunk', metadata: { source: 'doc-2' } },
			{ id: 'chunk-4', label: 'Authentication', type: 'chunk', metadata: { source: 'doc-3' } },

			// Entities
			{ id: 'entity-1', label: 'RAG System', type: 'entity' },
			{ id: 'entity-2', label: 'Vector Database', type: 'entity' },
			{ id: 'entity-3', label: 'LLM Provider', type: 'entity' },

			// Concepts
			{ id: 'concept-1', label: 'Embeddings', type: 'concept' },
			{ id: 'concept-2', label: 'Semantic Search', type: 'concept' },
			{ id: 'concept-3', label: 'Retrieval', type: 'concept' },

			// Topics
			{ id: 'topic-1', label: 'Architecture', type: 'topic' },
			{ id: 'topic-2', label: 'Security', type: 'topic' },
			{ id: 'topic-3', label: 'Performance', type: 'topic' }
		];

		const edges: GraphEdge[] = [
			// Document contains chunks
			{ id: 'e1', source: 'doc-1', target: 'chunk-1', type: 'contains', weight: 1 },
			{ id: 'e2', source: 'doc-1', target: 'chunk-2', type: 'contains', weight: 1 },
			{ id: 'e3', source: 'doc-2', target: 'chunk-3', type: 'contains', weight: 1 },
			{ id: 'e4', source: 'doc-3', target: 'chunk-4', type: 'contains', weight: 1 },

			// Chunks reference entities
			{ id: 'e5', source: 'chunk-1', target: 'entity-1', type: 'references', weight: 0.9 },
			{ id: 'e6', source: 'chunk-2', target: 'entity-2', type: 'references', weight: 0.8 },
			{ id: 'e7', source: 'chunk-2', target: 'entity-3', type: 'references', weight: 0.7 },
			{ id: 'e8', source: 'chunk-4', target: 'entity-1', type: 'references', weight: 0.6 },

			// Entity relationships
			{ id: 'e9', source: 'entity-1', target: 'entity-2', type: 'related', weight: 0.85 },
			{ id: 'e10', source: 'entity-1', target: 'entity-3', type: 'related', weight: 0.75 },

			// Concept connections
			{ id: 'e11', source: 'concept-1', target: 'concept-2', type: 'similar', weight: 0.9 },
			{ id: 'e12', source: 'concept-2', target: 'concept-3', type: 'similar', weight: 0.8 },
			{ id: 'e13', source: 'entity-2', target: 'concept-1', type: 'related', weight: 0.7 },

			// Topic relationships
			{ id: 'e14', source: 'doc-1', target: 'topic-1', type: 'related', weight: 0.9 },
			{ id: 'e15', source: 'doc-3', target: 'topic-2', type: 'related', weight: 0.8 },
			{ id: 'e16', source: 'chunk-2', target: 'topic-3', type: 'related', weight: 0.7 }
		];

		return { nodes, edges };
	}

	function handleNodeClick(event: CustomEvent<{ node: GraphNode }>) {
		const { node } = event.detail;
		if (node) {
			selectedNode = node;
			// Get edges connected to this node
			connectedEdges = graphData.edges.filter((edge) => {
				const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
				const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;
				return sourceId === node.id || targetId === node.id;
			});
		} else {
			selectedNode = null;
			connectedEdges = [];
		}
	}

	function handleNodeHover(event: CustomEvent<{ node: GraphNode | null }>) {
		hoveredNode = event.detail.node;
	}

	function handleLayoutChange(event: CustomEvent<GraphLayout>) {
		layout = event.detail;
	}

	function handleFilterChange(event: CustomEvent<GraphFilters>) {
		filters = event.detail;
	}

	function handleViewChange(event: CustomEvent<{ zoom: number; panX: number; panY: number }>) {
		zoom = event.detail.zoom;
	}

	function handleZoomIn() {
		graphViewRef?.zoomIn();
	}

	function handleZoomOut() {
		graphViewRef?.zoomOut();
	}

	function handleFitView() {
		graphViewRef?.fitView();
	}

	function handleReset() {
		graphViewRef?.resetView();
		selectedNode = null;
		connectedEdges = [];
	}

	function handleExport(event: CustomEvent<{ format: 'png' | 'svg' }>) {
		// TODO: Implement export functionality
		addToast({
			type: 'info',
			title: 'Export',
			message: `Export to ${event.detail.format.toUpperCase()} coming soon`
		});
	}

	function handleNavigate(event: CustomEvent<{ nodeId: string }>) {
		const node = graphData.nodes.find((n) => n.id === event.detail.nodeId);
		if (node) {
			selectedNode = node;
			connectedEdges = graphData.edges.filter((edge) => {
				const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
				const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;
				return sourceId === node.id || targetId === node.id;
			});
		}
	}

	function handleCloseDetails() {
		selectedNode = null;
		connectedEdges = [];
	}

	onMount(() => {
		loadGraphData();
	});
</script>

<svelte:head>
	<title>Knowledge Graph - ragged</title>
</svelte:head>

<div class="graph-page">
	<div class="graph-page__header">
		<div class="graph-page__title-section">
			<h1 class="graph-page__title">Knowledge Graph</h1>
			<p class="graph-page__subtitle">
				Visualise relationships between documents, entities, and concepts
			</p>
		</div>

		<div class="graph-page__controls">
			<Button variant="ghost" size="sm" on:click={loadGraphData}>
				<svg
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
				>
					<polyline points="23 4 23 10 17 10" />
					<polyline points="1 20 1 14 7 14" />
					<path
						d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"
					/>
				</svg>
				Refresh
			</Button>
		</div>
	</div>

	{#if error}
		<div class="graph-page__error" role="alert">
			<svg
				width="48"
				height="48"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="1.5"
			>
				<circle cx="12" cy="12" r="10" />
				<line x1="12" y1="8" x2="12" y2="12" />
				<line x1="12" y1="16" x2="12.01" y2="16" />
			</svg>
			<p>{error}</p>
			<Button variant="primary" size="sm" on:click={loadGraphData}>Try again</Button>
		</div>
	{:else if loading}
		<div class="graph-page__loading">
			<div class="graph-page__loading-content">
				<Skeleton height="600px" />
			</div>
			<div class="graph-page__loading-sidebar">
				<Skeleton height="300px" />
			</div>
		</div>
	{:else}
		<div class="graph-page__content">
			<div class="graph-page__sidebar graph-page__sidebar--left">
				<GraphControls
					{layout}
					{filters}
					{zoom}
					on:layoutChange={handleLayoutChange}
					on:filterChange={handleFilterChange}
					on:zoomIn={handleZoomIn}
					on:zoomOut={handleZoomOut}
					on:fitView={handleFitView}
					on:reset={handleReset}
					on:export={handleExport}
				/>
			</div>

			<div class="graph-page__main">
				<GraphView
					bind:this={graphViewRef}
					data={filteredData}
					{layout}
					{selectedNode}
					on:nodeClick={handleNodeClick}
					on:nodeHover={handleNodeHover}
					on:viewChange={handleViewChange}
				/>

				<!-- Stats overlay -->
				<div class="graph-page__stats">
					<span class="graph-page__stat">
						<strong>{filteredData.nodes.length}</strong> nodes
					</span>
					<span class="graph-page__stat">
						<strong>{filteredData.edges.length}</strong> edges
					</span>
				</div>
			</div>

			<div class="graph-page__sidebar graph-page__sidebar--right">
				<NodeDetails
					node={selectedNode}
					{connectedEdges}
					on:close={handleCloseDetails}
					on:navigate={handleNavigate}
				/>
			</div>
		</div>
	{/if}
</div>

<style>
	.graph-page {
		display: flex;
		flex-direction: column;
		height: 100%;
		min-height: calc(100vh - 120px);
	}

	.graph-page__header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: var(--space-4);
		padding-bottom: var(--space-4);
		flex-wrap: wrap;
	}

	.graph-page__title-section {
		flex: 1;
	}

	.graph-page__title {
		margin: 0;
		font-size: var(--font-size-3xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-text-primary);
	}

	.graph-page__subtitle {
		margin: var(--space-2) 0 0;
		font-size: var(--font-size-lg);
		color: var(--color-text-muted);
	}

	.graph-page__controls {
		display: flex;
		align-items: center;
		gap: var(--space-3);
	}

	.graph-page__error {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--space-4);
		flex: 1;
		padding: var(--space-8);
		text-align: center;
		color: var(--color-danger);
		background-color: var(--color-danger-light);
		border-radius: var(--radius-lg);
	}

	.graph-page__error svg {
		opacity: 0.7;
	}

	.graph-page__loading {
		display: flex;
		gap: var(--space-4);
		flex: 1;
	}

	.graph-page__loading-content {
		flex: 1;
	}

	.graph-page__loading-sidebar {
		width: 300px;
	}

	.graph-page__content {
		display: flex;
		gap: var(--space-4);
		flex: 1;
		min-height: 0;
	}

	.graph-page__sidebar {
		flex-shrink: 0;
	}

	.graph-page__sidebar--left {
		width: 220px;
	}

	.graph-page__sidebar--right {
		width: 300px;
	}

	.graph-page__main {
		flex: 1;
		position: relative;
		min-width: 0;
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
		overflow: hidden;
	}

	.graph-page__stats {
		position: absolute;
		bottom: var(--space-4);
		left: var(--space-4);
		display: flex;
		gap: var(--space-4);
		padding: var(--space-2) var(--space-3);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.graph-page__stat strong {
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
	}

	@media (max-width: 1024px) {
		.graph-page__content {
			flex-wrap: wrap;
		}

		.graph-page__sidebar--left {
			width: 100%;
			order: 2;
		}

		.graph-page__sidebar--right {
			width: 100%;
			order: 3;
		}

		.graph-page__main {
			width: 100%;
			min-height: 500px;
			order: 1;
		}
	}

	@media (max-width: 640px) {
		.graph-page__header {
			flex-direction: column;
			align-items: stretch;
		}

		.graph-page__controls {
			justify-content: flex-end;
		}

		.graph-page__stats {
			bottom: var(--space-2);
			left: var(--space-2);
		}
	}
</style>
