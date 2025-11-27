/**
 * Graph Layout Utilities
 * ragged WebUI v0.9.3
 *
 * Layout algorithms for knowledge graph visualisation
 */

import * as d3 from 'd3';
import type { GraphNode, GraphEdge, GraphLayout, LayoutSettings } from './types';

export interface SimulationOptions {
	width: number;
	height: number;
	layout: GraphLayout;
	onTick?: () => void;
	onEnd?: () => void;
}

const DEFAULT_SETTINGS: LayoutSettings = {
	linkDistance: 100,
	chargeStrength: -300,
	centerStrength: 0.1,
	collisionRadius: 30
};

/**
 * Create a D3 force simulation for the graph
 */
export function createSimulation(
	nodes: GraphNode[],
	edges: GraphEdge[],
	options: SimulationOptions
): d3.Simulation<GraphNode, GraphEdge> {
	const { width, height, layout, onTick, onEnd } = options;
	const settings = { ...DEFAULT_SETTINGS, ...layout.settings };

	const simulation = d3
		.forceSimulation<GraphNode>(nodes)
		.force(
			'link',
			d3
				.forceLink<GraphNode, GraphEdge>(edges)
				.id((d) => d.id)
				.distance(settings.linkDistance!)
		)
		.force('charge', d3.forceManyBody().strength(settings.chargeStrength!))
		.force('center', d3.forceCenter(width / 2, height / 2).strength(settings.centerStrength!))
		.force('collision', d3.forceCollide().radius(settings.collisionRadius!));

	// Apply layout-specific forces
	if (layout.type === 'radial') {
		simulation.force(
			'radial',
			d3.forceRadial(Math.min(width, height) / 3, width / 2, height / 2).strength(0.5)
		);
	}

	if (onTick) {
		simulation.on('tick', onTick);
	}

	if (onEnd) {
		simulation.on('end', onEnd);
	}

	return simulation;
}

/**
 * Calculate hierarchical layout positions
 */
export function calculateHierarchicalLayout(
	nodes: GraphNode[],
	edges: GraphEdge[],
	width: number,
	height: number
): GraphNode[] {
	// Build adjacency map
	const children = new Map<string, string[]>();
	const parents = new Map<string, string>();

	edges.forEach((edge) => {
		const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
		const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;

		if (edge.type === 'contains' || edge.type === 'parent') {
			if (!children.has(sourceId)) {
				children.set(sourceId, []);
			}
			children.get(sourceId)!.push(targetId);
			parents.set(targetId, sourceId);
		}
	});

	// Find root nodes (no parents)
	const roots = nodes.filter((n) => !parents.has(n.id));

	// Calculate levels
	const levels = new Map<string, number>();
	const queue = roots.map((r) => ({ id: r.id, level: 0 }));

	while (queue.length > 0) {
		const { id, level } = queue.shift()!;
		levels.set(id, level);

		const nodeChildren = children.get(id) || [];
		nodeChildren.forEach((childId) => {
			if (!levels.has(childId)) {
				queue.push({ id: childId, level: level + 1 });
			}
		});
	}

	// Group by level
	const levelGroups = new Map<number, string[]>();
	levels.forEach((level, id) => {
		if (!levelGroups.has(level)) {
			levelGroups.set(level, []);
		}
		levelGroups.get(level)!.push(id);
	});

	const maxLevel = Math.max(...levels.values(), 0);
	const levelHeight = height / (maxLevel + 2);

	// Position nodes
	return nodes.map((node) => {
		const level = levels.get(node.id) ?? 0;
		const levelNodes = levelGroups.get(level) || [node.id];
		const index = levelNodes.indexOf(node.id);
		const levelWidth = width / (levelNodes.length + 1);

		return {
			...node,
			x: levelWidth * (index + 1),
			y: levelHeight * (level + 1),
			fx: levelWidth * (index + 1),
			fy: levelHeight * (level + 1)
		};
	});
}

/**
 * Apply zoom transform to SVG
 */
export function applyZoom(
	svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
	container: d3.Selection<SVGGElement, unknown, null, undefined>,
	onZoom?: (transform: d3.ZoomTransform) => void
): d3.ZoomBehavior<SVGSVGElement, unknown> {
	const zoom = d3
		.zoom<SVGSVGElement, unknown>()
		.scaleExtent([0.1, 4])
		.on('zoom', (event) => {
			container.attr('transform', event.transform.toString());
			if (onZoom) {
				onZoom(event.transform);
			}
		});

	svg.call(zoom);
	return zoom;
}

/**
 * Fit graph to viewport
 */
export function fitToViewport(
	nodes: GraphNode[],
	width: number,
	height: number,
	padding = 50
): d3.ZoomTransform {
	if (nodes.length === 0) {
		return d3.zoomIdentity;
	}

	const xExtent = d3.extent(nodes, (d) => d.x) as [number, number];
	const yExtent = d3.extent(nodes, (d) => d.y) as [number, number];

	const graphWidth = xExtent[1] - xExtent[0];
	const graphHeight = yExtent[1] - yExtent[0];

	const scale = Math.min(
		(width - padding * 2) / graphWidth,
		(height - padding * 2) / graphHeight,
		1
	);

	const centerX = (xExtent[0] + xExtent[1]) / 2;
	const centerY = (yExtent[0] + yExtent[1]) / 2;

	return d3.zoomIdentity
		.translate(width / 2, height / 2)
		.scale(scale)
		.translate(-centerX, -centerY);
}
