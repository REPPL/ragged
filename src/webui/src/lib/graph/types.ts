/**
 * Graph Types
 * ragged WebUI v0.9.3
 *
 * Type definitions for knowledge graph visualisation
 */

export interface GraphNode {
	id: string;
	label: string;
	type: NodeType;
	metadata?: Record<string, unknown>;
	x?: number;
	y?: number;
	fx?: number | null;
	fy?: number | null;
}

export interface GraphEdge {
	id: string;
	source: string | GraphNode;
	target: string | GraphNode;
	type: EdgeType;
	weight?: number;
	label?: string;
}

export type NodeType = 'document' | 'chunk' | 'entity' | 'concept' | 'topic';
export type EdgeType = 'contains' | 'references' | 'similar' | 'related' | 'parent';

export interface GraphData {
	nodes: GraphNode[];
	edges: GraphEdge[];
}

export interface GraphLayout {
	type: 'force' | 'radial' | 'hierarchical';
	settings?: LayoutSettings;
}

export interface LayoutSettings {
	linkDistance?: number;
	chargeStrength?: number;
	centerStrength?: number;
	collisionRadius?: number;
}

export interface GraphFilters {
	nodeTypes: NodeType[];
	edgeTypes: EdgeType[];
	minWeight?: number;
	searchQuery?: string;
}

export interface ViewState {
	zoom: number;
	panX: number;
	panY: number;
}

export const NODE_COLOURS: Record<NodeType, string> = {
	document: '#4f46e5',
	chunk: '#0891b2',
	entity: '#059669',
	concept: '#d97706',
	topic: '#dc2626'
};

export const NODE_ICONS: Record<NodeType, string> = {
	document: 'file-text',
	chunk: 'layers',
	entity: 'user',
	concept: 'lightbulb',
	topic: 'hash'
};

export const EDGE_COLOURS: Record<EdgeType, string> = {
	contains: '#94a3b8',
	references: '#3b82f6',
	similar: '#10b981',
	related: '#f59e0b',
	parent: '#8b5cf6'
};
