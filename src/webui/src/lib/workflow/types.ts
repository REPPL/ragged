/**
 * Workflow Types
 * ragged WebUI v0.9.4
 *
 * Type definitions for visual workflow editor
 */

export interface WorkflowNode {
	id: string;
	type: NodeType;
	label: string;
	x: number;
	y: number;
	width: number;
	height: number;
	config: NodeConfig;
	inputs: NodePort[];
	outputs: NodePort[];
}

export interface NodePort {
	id: string;
	name: string;
	type: PortType;
	connected?: boolean;
}

export interface WorkflowConnection {
	id: string;
	sourceNodeId: string;
	sourcePortId: string;
	targetNodeId: string;
	targetPortId: string;
}

export interface Workflow {
	id: string;
	name: string;
	description?: string;
	nodes: WorkflowNode[];
	connections: WorkflowConnection[];
	createdAt: string;
	updatedAt: string;
}

export type NodeType =
	| 'document-input'
	| 'text-input'
	| 'query-input'
	| 'embedding'
	| 'retrieval'
	| 'reranker'
	| 'llm'
	| 'prompt-template'
	| 'filter'
	| 'merge'
	| 'split'
	| 'output'
	| 'custom';

export type PortType = 'document' | 'text' | 'embedding' | 'query' | 'any';

export interface NodeConfig {
	[key: string]: unknown;
}

export interface NodeDefinition {
	type: NodeType;
	label: string;
	description: string;
	category: NodeCategory;
	icon: string;
	colour: string;
	inputs: Omit<NodePort, 'id' | 'connected'>[];
	outputs: Omit<NodePort, 'id' | 'connected'>[];
	defaultConfig: NodeConfig;
	configSchema?: ConfigField[];
}

export interface ConfigField {
	key: string;
	label: string;
	type: 'text' | 'number' | 'select' | 'boolean' | 'textarea';
	options?: { value: string; label: string }[];
	default?: unknown;
	required?: boolean;
	placeholder?: string;
}

export type NodeCategory = 'input' | 'processing' | 'retrieval' | 'output' | 'utility';

export interface CanvasState {
	zoom: number;
	panX: number;
	panY: number;
}

export interface DragState {
	isDragging: boolean;
	nodeId: string | null;
	startX: number;
	startY: number;
	offsetX: number;
	offsetY: number;
}

export interface ConnectionState {
	isConnecting: boolean;
	sourceNodeId: string | null;
	sourcePortId: string | null;
	mouseX: number;
	mouseY: number;
}

export const NODE_COLOURS: Record<NodeCategory, string> = {
	input: '#4f46e5',
	processing: '#059669',
	retrieval: '#0891b2',
	output: '#dc2626',
	utility: '#d97706'
};

export const PORT_COLOURS: Record<PortType, string> = {
	document: '#4f46e5',
	text: '#059669',
	embedding: '#0891b2',
	query: '#d97706',
	any: '#6b7280'
};
