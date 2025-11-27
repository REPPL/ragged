<!--
  Graph View Component
  ragged WebUI v0.9.3

  D3.js force-directed knowledge graph visualisation
-->
<script lang="ts">
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import * as d3 from 'd3';
	import type {
		GraphNode,
		GraphEdge,
		GraphData,
		GraphLayout,
		NodeType,
		ViewState
	} from '$lib/graph/types';
	import { NODE_COLOURS, EDGE_COLOURS } from '$lib/graph/types';
	import { createSimulation, applyZoom, fitToViewport } from '$lib/graph/layout';

	export let data: GraphData = { nodes: [], edges: [] };
	export let layout: GraphLayout = { type: 'force' };
	export let selectedNode: GraphNode | null = null;
	export let highlightedNodes: Set<string> = new Set();

	const dispatch = createEventDispatcher<{
		nodeClick: { node: GraphNode };
		nodeHover: { node: GraphNode | null };
		viewChange: ViewState;
	}>();

	let container: HTMLDivElement;
	let svg: d3.Selection<SVGSVGElement, unknown, null, undefined>;
	let g: d3.Selection<SVGGElement, unknown, null, undefined>;
	let simulation: d3.Simulation<GraphNode, GraphEdge> | null = null;
	let zoom: d3.ZoomBehavior<SVGSVGElement, unknown> | null = null;

	let width = 800;
	let height = 600;
	let currentTransform = d3.zoomIdentity;

	$: if (svg && data.nodes.length > 0) {
		updateGraph();
	}

	function updateGraph() {
		if (!svg || !g) return;

		// Stop previous simulation
		if (simulation) {
			simulation.stop();
		}

		// Clear previous elements
		g.selectAll('*').remove();

		// Create edge lines
		const links = g
			.append('g')
			.attr('class', 'links')
			.selectAll('line')
			.data(data.edges)
			.enter()
			.append('line')
			.attr('stroke', (d) => EDGE_COLOURS[d.type] || '#94a3b8')
			.attr('stroke-opacity', 0.6)
			.attr('stroke-width', (d) => Math.sqrt(d.weight || 1));

		// Create node groups
		const nodes = g
			.append('g')
			.attr('class', 'nodes')
			.selectAll('g')
			.data(data.nodes)
			.enter()
			.append('g')
			.attr('class', 'node')
			.attr('cursor', 'pointer')
			.call(
				d3
					.drag<SVGGElement, GraphNode>()
					.on('start', dragstarted)
					.on('drag', dragged)
					.on('end', dragended)
			)
			.on('click', (event, d) => {
				event.stopPropagation();
				dispatch('nodeClick', { node: d });
			})
			.on('mouseenter', (event, d) => {
				dispatch('nodeHover', { node: d });
				highlightConnected(d.id);
			})
			.on('mouseleave', () => {
				dispatch('nodeHover', { node: null });
				clearHighlight();
			});

		// Node circles
		nodes
			.append('circle')
			.attr('r', (d) => getNodeRadius(d.type))
			.attr('fill', (d) => NODE_COLOURS[d.type] || '#6b7280')
			.attr('stroke', '#fff')
			.attr('stroke-width', 2)
			.attr('class', 'node-circle');

		// Node labels
		nodes
			.append('text')
			.attr('dy', (d) => getNodeRadius(d.type) + 14)
			.attr('text-anchor', 'middle')
			.attr('font-size', '12px')
			.attr('fill', 'var(--color-text-secondary)')
			.attr('class', 'node-label')
			.text((d) => truncateLabel(d.label, 20));

		// Create simulation
		simulation = createSimulation(data.nodes, data.edges, {
			width,
			height,
			layout,
			onTick: () => {
				links
					.attr('x1', (d) => (d.source as GraphNode).x!)
					.attr('y1', (d) => (d.source as GraphNode).y!)
					.attr('x2', (d) => (d.target as GraphNode).x!)
					.attr('y2', (d) => (d.target as GraphNode).y!);

				nodes.attr('transform', (d) => `translate(${d.x},${d.y})`);
			}
		});

		// Update selection styling
		updateSelection();
	}

	function getNodeRadius(type: NodeType): number {
		const radii: Record<NodeType, number> = {
			document: 20,
			chunk: 12,
			entity: 16,
			concept: 14,
			topic: 18
		};
		return radii[type] || 14;
	}

	function truncateLabel(label: string, maxLength: number): string {
		if (label.length <= maxLength) return label;
		return label.substring(0, maxLength - 3) + '...';
	}

	function dragstarted(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>) {
		if (!event.active && simulation) {
			simulation.alphaTarget(0.3).restart();
		}
		event.subject.fx = event.subject.x;
		event.subject.fy = event.subject.y;
	}

	function dragged(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>) {
		event.subject.fx = event.x;
		event.subject.fy = event.y;
	}

	function dragended(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>) {
		if (!event.active && simulation) {
			simulation.alphaTarget(0);
		}
		event.subject.fx = null;
		event.subject.fy = null;
	}

	function highlightConnected(nodeId: string) {
		const connectedIds = new Set<string>([nodeId]);
		data.edges.forEach((edge) => {
			const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
			const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;
			if (sourceId === nodeId) connectedIds.add(targetId);
			if (targetId === nodeId) connectedIds.add(sourceId);
		});

		g.selectAll('.node').attr('opacity', (d: any) => (connectedIds.has(d.id) ? 1 : 0.3));
		g.selectAll('.links line').attr('opacity', (d: any) => {
			const sourceId = typeof d.source === 'string' ? d.source : d.source.id;
			const targetId = typeof d.target === 'string' ? d.target : d.target.id;
			return sourceId === nodeId || targetId === nodeId ? 1 : 0.1;
		});
	}

	function clearHighlight() {
		g.selectAll('.node').attr('opacity', 1);
		g.selectAll('.links line').attr('opacity', 0.6);
	}

	function updateSelection() {
		if (!g) return;

		g.selectAll('.node-circle')
			.attr('stroke', (d: any) => (selectedNode?.id === d.id ? '#000' : '#fff'))
			.attr('stroke-width', (d: any) => (selectedNode?.id === d.id ? 3 : 2));
	}

	$: if (g && selectedNode !== undefined) {
		updateSelection();
	}

	export function zoomIn() {
		if (svg && zoom) {
			svg.transition().duration(300).call(zoom.scaleBy, 1.5);
		}
	}

	export function zoomOut() {
		if (svg && zoom) {
			svg.transition().duration(300).call(zoom.scaleBy, 0.67);
		}
	}

	export function fitView() {
		if (svg && zoom && data.nodes.length > 0) {
			const transform = fitToViewport(data.nodes, width, height);
			svg.transition().duration(500).call(zoom.transform, transform);
		}
	}

	export function resetView() {
		if (svg && zoom) {
			svg.transition().duration(300).call(zoom.transform, d3.zoomIdentity);
		}
	}

	function handleResize() {
		if (container) {
			width = container.clientWidth;
			height = container.clientHeight;

			if (svg) {
				svg.attr('width', width).attr('height', height);
			}

			if (simulation) {
				simulation.force('center', d3.forceCenter(width / 2, height / 2));
				simulation.alpha(0.3).restart();
			}
		}
	}

	let resizeObserver: ResizeObserver | null = null;

	onMount(() => {
		if (container) {
			width = container.clientWidth;
			height = container.clientHeight;

			svg = d3
				.select(container)
				.append('svg')
				.attr('width', width)
				.attr('height', height)
				.attr('viewBox', `0 0 ${width} ${height}`);

			// Add background for pan/zoom
			svg
				.append('rect')
				.attr('width', '100%')
				.attr('height', '100%')
				.attr('fill', 'transparent')
				.on('click', () => dispatch('nodeClick', { node: null as any }));

			g = svg.append('g');

			zoom = applyZoom(svg, g, (transform) => {
				currentTransform = transform;
				dispatch('viewChange', {
					zoom: transform.k,
					panX: transform.x,
					panY: transform.y
				});
			});

			resizeObserver = new ResizeObserver(handleResize);
			resizeObserver.observe(container);

			if (data.nodes.length > 0) {
				updateGraph();
			}
		}
	});

	onDestroy(() => {
		if (simulation) {
			simulation.stop();
		}
		if (resizeObserver) {
			resizeObserver.disconnect();
		}
	});
</script>

<div bind:this={container} class="graph-view">
	{#if data.nodes.length === 0}
		<div class="graph-view__empty">
			<svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
				<circle cx="12" cy="12" r="10" />
				<circle cx="12" cy="12" r="3" />
				<line x1="12" y1="2" x2="12" y2="5" />
				<line x1="12" y1="19" x2="12" y2="22" />
				<line x1="2" y1="12" x2="5" y2="12" />
				<line x1="19" y1="12" x2="22" y2="12" />
			</svg>
			<h3>No graph data</h3>
			<p>Upload documents to see their relationships</p>
		</div>
	{/if}
</div>

<style>
	.graph-view {
		width: 100%;
		height: 100%;
		min-height: 400px;
		position: relative;
		background-color: var(--color-bg);
		border-radius: var(--radius-lg);
		overflow: hidden;
	}

	.graph-view :global(svg) {
		display: block;
	}

	.graph-view :global(.node-label) {
		pointer-events: none;
		user-select: none;
	}

	.graph-view :global(.links line) {
		pointer-events: none;
	}

	.graph-view__empty {
		position: absolute;
		inset: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--space-4);
		color: var(--color-text-muted);
		text-align: center;
	}

	.graph-view__empty svg {
		opacity: 0.5;
	}

	.graph-view__empty h3 {
		margin: 0;
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-secondary);
	}

	.graph-view__empty p {
		margin: 0;
	}
</style>
