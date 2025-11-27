/**
 * Workflow Connections
 * ragged WebUI v0.9.4
 *
 * Utilities for managing workflow node connections
 */

import type { WorkflowNode, WorkflowConnection, NodePort, PortType } from './types';

/**
 * Check if two port types are compatible for connection
 */
export function arePortsCompatible(sourceType: PortType, targetType: PortType): boolean {
	// 'any' type is compatible with everything
	if (sourceType === 'any' || targetType === 'any') {
		return true;
	}

	// Same types are always compatible
	if (sourceType === targetType) {
		return true;
	}

	// Text and query are often interchangeable
	if (
		(sourceType === 'text' && targetType === 'query') ||
		(sourceType === 'query' && targetType === 'text')
	) {
		return true;
	}

	return false;
}

/**
 * Create a new connection between nodes
 */
export function createConnection(
	sourceNodeId: string,
	sourcePortId: string,
	targetNodeId: string,
	targetPortId: string
): WorkflowConnection {
	return {
		id: `conn-${Date.now()}-${Math.random().toString(36).substring(7)}`,
		sourceNodeId,
		sourcePortId,
		targetNodeId,
		targetPortId
	};
}

/**
 * Check if a connection already exists
 */
export function connectionExists(
	connections: WorkflowConnection[],
	sourceNodeId: string,
	sourcePortId: string,
	targetNodeId: string,
	targetPortId: string
): boolean {
	return connections.some(
		(conn) =>
			conn.sourceNodeId === sourceNodeId &&
			conn.sourcePortId === sourcePortId &&
			conn.targetNodeId === targetNodeId &&
			conn.targetPortId === targetPortId
	);
}

/**
 * Check if a target port already has an incoming connection
 */
export function hasIncomingConnection(
	connections: WorkflowConnection[],
	targetNodeId: string,
	targetPortId: string
): boolean {
	return connections.some(
		(conn) => conn.targetNodeId === targetNodeId && conn.targetPortId === targetPortId
	);
}

/**
 * Get all connections for a specific node
 */
export function getNodeConnections(
	connections: WorkflowConnection[],
	nodeId: string
): WorkflowConnection[] {
	return connections.filter(
		(conn) => conn.sourceNodeId === nodeId || conn.targetNodeId === nodeId
	);
}

/**
 * Remove all connections for a specific node
 */
export function removeNodeConnections(
	connections: WorkflowConnection[],
	nodeId: string
): WorkflowConnection[] {
	return connections.filter(
		(conn) => conn.sourceNodeId !== nodeId && conn.targetNodeId !== nodeId
	);
}

/**
 * Calculate the SVG path for a connection between two points
 */
export function calculateConnectionPath(
	startX: number,
	startY: number,
	endX: number,
	endY: number
): string {
	const midX = (startX + endX) / 2;
	const dx = Math.abs(endX - startX);
	const controlOffset = Math.min(dx * 0.5, 100);

	// Bezier curve for smooth connection
	return `M ${startX} ${startY} C ${startX + controlOffset} ${startY}, ${endX - controlOffset} ${endY}, ${endX} ${endY}`;
}

/**
 * Get port position on a node
 */
export function getPortPosition(
	node: WorkflowNode,
	port: NodePort,
	isOutput: boolean
): { x: number; y: number } {
	const ports = isOutput ? node.outputs : node.inputs;
	const portIndex = ports.findIndex((p) => p.id === port.id);
	const portCount = ports.length;

	const headerHeight = 40;
	const portSpacing = 24;
	const portStartY = headerHeight + 12;

	const x = isOutput ? node.x + node.width : node.x;
	const y = node.y + portStartY + portIndex * portSpacing;

	return { x, y };
}

/**
 * Find a port by ID in a node
 */
export function findPort(
	node: WorkflowNode,
	portId: string
): { port: NodePort; isOutput: boolean } | null {
	const inputPort = node.inputs.find((p) => p.id === portId);
	if (inputPort) {
		return { port: inputPort, isOutput: false };
	}

	const outputPort = node.outputs.find((p) => p.id === portId);
	if (outputPort) {
		return { port: outputPort, isOutput: true };
	}

	return null;
}

/**
 * Validate workflow for cycles (prevent infinite loops)
 */
export function hasCycles(nodes: WorkflowNode[], connections: WorkflowConnection[]): boolean {
	const adjacency = new Map<string, string[]>();

	// Build adjacency list
	nodes.forEach((node) => {
		adjacency.set(node.id, []);
	});

	connections.forEach((conn) => {
		const targets = adjacency.get(conn.sourceNodeId);
		if (targets) {
			targets.push(conn.targetNodeId);
		}
	});

	// DFS to detect cycles
	const visited = new Set<string>();
	const recursionStack = new Set<string>();

	function dfs(nodeId: string): boolean {
		visited.add(nodeId);
		recursionStack.add(nodeId);

		const neighbours = adjacency.get(nodeId) || [];
		for (const neighbour of neighbours) {
			if (!visited.has(neighbour)) {
				if (dfs(neighbour)) {
					return true;
				}
			} else if (recursionStack.has(neighbour)) {
				return true;
			}
		}

		recursionStack.delete(nodeId);
		return false;
	}

	for (const node of nodes) {
		if (!visited.has(node.id)) {
			if (dfs(node.id)) {
				return true;
			}
		}
	}

	return false;
}

/**
 * Get execution order (topological sort)
 */
export function getExecutionOrder(
	nodes: WorkflowNode[],
	connections: WorkflowConnection[]
): string[] {
	const inDegree = new Map<string, number>();
	const adjacency = new Map<string, string[]>();

	// Initialise
	nodes.forEach((node) => {
		inDegree.set(node.id, 0);
		adjacency.set(node.id, []);
	});

	// Build graph
	connections.forEach((conn) => {
		const targets = adjacency.get(conn.sourceNodeId);
		if (targets) {
			targets.push(conn.targetNodeId);
		}
		inDegree.set(conn.targetNodeId, (inDegree.get(conn.targetNodeId) || 0) + 1);
	});

	// Kahn's algorithm
	const queue: string[] = [];
	const result: string[] = [];

	inDegree.forEach((degree, nodeId) => {
		if (degree === 0) {
			queue.push(nodeId);
		}
	});

	while (queue.length > 0) {
		const nodeId = queue.shift()!;
		result.push(nodeId);

		const neighbours = adjacency.get(nodeId) || [];
		for (const neighbour of neighbours) {
			const newDegree = (inDegree.get(neighbour) || 0) - 1;
			inDegree.set(neighbour, newDegree);
			if (newDegree === 0) {
				queue.push(neighbour);
			}
		}
	}

	return result;
}
