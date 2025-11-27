<!--
  Workflow Canvas Component
  ragged WebUI v0.9.4

  Interactive canvas for building RAG workflows
-->
<script lang="ts">
	import { createEventDispatcher, onMount, onDestroy } from 'svelte';
	import type {
		WorkflowNode,
		WorkflowConnection,
		CanvasState,
		DragState,
		ConnectionState,
		NodePort
	} from '$lib/workflow/types';
	import { NODE_COLOURS, PORT_COLOURS } from '$lib/workflow/types';
	import { NODE_DEFINITIONS } from '$lib/workflow/nodes';
	import {
		calculateConnectionPath,
		getPortPosition,
		arePortsCompatible,
		hasIncomingConnection
	} from '$lib/workflow/connections';

	export let nodes: WorkflowNode[] = [];
	export let connections: WorkflowConnection[] = [];
	export let selectedNodeId: string | null = null;
	export let zoom = 1;

	const dispatch = createEventDispatcher<{
		nodeSelect: { nodeId: string | null };
		nodeMove: { nodeId: string; x: number; y: number };
		nodeDelete: { nodeId: string };
		connectionCreate: { connection: WorkflowConnection };
		connectionDelete: { connectionId: string };
		viewChange: CanvasState;
	}>();

	let container: HTMLDivElement;
	let svg: SVGSVGElement;
	let width = 800;
	let height = 600;

	let canvasState: CanvasState = {
		zoom: 1,
		panX: 0,
		panY: 0
	};

	let dragState: DragState = {
		isDragging: false,
		nodeId: null,
		startX: 0,
		startY: 0,
		offsetX: 0,
		offsetY: 0
	};

	let connectionState: ConnectionState = {
		isConnecting: false,
		sourceNodeId: null,
		sourcePortId: null,
		mouseX: 0,
		mouseY: 0
	};

	let isPanning = false;
	let panStartX = 0;
	let panStartY = 0;

	$: canvasState.zoom = zoom;

	$: viewBox = `${-canvasState.panX / canvasState.zoom} ${-canvasState.panY / canvasState.zoom} ${width / canvasState.zoom} ${height / canvasState.zoom}`;

	function handleMouseDown(event: MouseEvent) {
		if (event.button === 1 || (event.button === 0 && event.shiftKey)) {
			// Middle click or shift+left click for panning
			isPanning = true;
			panStartX = event.clientX - canvasState.panX;
			panStartY = event.clientY - canvasState.panY;
			event.preventDefault();
		}
	}

	function handleMouseMove(event: MouseEvent) {
		if (isPanning) {
			canvasState.panX = event.clientX - panStartX;
			canvasState.panY = event.clientY - panStartY;
			dispatch('viewChange', canvasState);
		}

		if (connectionState.isConnecting) {
			const rect = svg.getBoundingClientRect();
			connectionState.mouseX =
				(event.clientX - rect.left - canvasState.panX) / canvasState.zoom;
			connectionState.mouseY =
				(event.clientY - rect.top - canvasState.panY) / canvasState.zoom;
		}

		if (dragState.isDragging && dragState.nodeId) {
			const rect = svg.getBoundingClientRect();
			const x =
				(event.clientX - rect.left - canvasState.panX) / canvasState.zoom -
				dragState.offsetX;
			const y =
				(event.clientY - rect.top - canvasState.panY) / canvasState.zoom -
				dragState.offsetY;

			dispatch('nodeMove', { nodeId: dragState.nodeId, x: Math.max(0, x), y: Math.max(0, y) });
		}
	}

	function handleMouseUp() {
		isPanning = false;

		if (dragState.isDragging) {
			dragState = {
				isDragging: false,
				nodeId: null,
				startX: 0,
				startY: 0,
				offsetX: 0,
				offsetY: 0
			};
		}

		if (connectionState.isConnecting) {
			connectionState = {
				isConnecting: false,
				sourceNodeId: null,
				sourcePortId: null,
				mouseX: 0,
				mouseY: 0
			};
		}
	}

	function handleWheel(event: WheelEvent) {
		event.preventDefault();
		const delta = event.deltaY > 0 ? 0.9 : 1.1;
		const newZoom = Math.min(Math.max(canvasState.zoom * delta, 0.25), 2);

		// Zoom towards mouse position
		const rect = svg.getBoundingClientRect();
		const mouseX = event.clientX - rect.left;
		const mouseY = event.clientY - rect.top;

		const scale = newZoom / canvasState.zoom;
		canvasState.panX = mouseX - (mouseX - canvasState.panX) * scale;
		canvasState.panY = mouseY - (mouseY - canvasState.panY) * scale;
		canvasState.zoom = newZoom;

		dispatch('viewChange', canvasState);
	}

	function handleNodeMouseDown(event: MouseEvent, node: WorkflowNode) {
		event.stopPropagation();
		const rect = svg.getBoundingClientRect();
		const mouseX = (event.clientX - rect.left - canvasState.panX) / canvasState.zoom;
		const mouseY = (event.clientY - rect.top - canvasState.panY) / canvasState.zoom;

		dragState = {
			isDragging: true,
			nodeId: node.id,
			startX: mouseX,
			startY: mouseY,
			offsetX: mouseX - node.x,
			offsetY: mouseY - node.y
		};

		dispatch('nodeSelect', { nodeId: node.id });
	}

	function handleNodeClick(event: MouseEvent, node: WorkflowNode) {
		event.stopPropagation();
		dispatch('nodeSelect', { nodeId: node.id });
	}

	function handleCanvasClick() {
		dispatch('nodeSelect', { nodeId: null });
	}

	function handlePortMouseDown(
		event: MouseEvent,
		node: WorkflowNode,
		port: NodePort,
		isOutput: boolean
	) {
		event.stopPropagation();
		if (isOutput) {
			const pos = getPortPosition(node, port, true);
			connectionState = {
				isConnecting: true,
				sourceNodeId: node.id,
				sourcePortId: port.id,
				mouseX: pos.x,
				mouseY: pos.y
			};
		}
	}

	function handlePortMouseUp(
		event: MouseEvent,
		node: WorkflowNode,
		port: NodePort,
		isOutput: boolean
	) {
		event.stopPropagation();
		if (connectionState.isConnecting && !isOutput) {
			// Check compatibility
			const sourceNode = nodes.find((n) => n.id === connectionState.sourceNodeId);
			const sourcePort = sourceNode?.outputs.find(
				(p) => p.id === connectionState.sourcePortId
			);

			if (sourceNode && sourcePort && arePortsCompatible(sourcePort.type, port.type)) {
				// Check if connection already exists or port already has input
				if (!hasIncomingConnection(connections, node.id, port.id)) {
					const newConnection = {
						id: `conn-${Date.now()}`,
						sourceNodeId: connectionState.sourceNodeId!,
						sourcePortId: connectionState.sourcePortId!,
						targetNodeId: node.id,
						targetPortId: port.id
					};
					dispatch('connectionCreate', { connection: newConnection });
				}
			}
		}

		connectionState = {
			isConnecting: false,
			sourceNodeId: null,
			sourcePortId: null,
			mouseX: 0,
			mouseY: 0
		};
	}

	function handleConnectionClick(event: MouseEvent, connectionId: string) {
		event.stopPropagation();
		dispatch('connectionDelete', { connectionId });
	}

	function handleKeyDown(event: KeyboardEvent) {
		if (event.key === 'Delete' || event.key === 'Backspace') {
			if (selectedNodeId) {
				dispatch('nodeDelete', { nodeId: selectedNodeId });
			}
		}
	}

	function getConnectionPath(connection: WorkflowConnection): string {
		const sourceNode = nodes.find((n) => n.id === connection.sourceNodeId);
		const targetNode = nodes.find((n) => n.id === connection.targetNodeId);

		if (!sourceNode || !targetNode) return '';

		const sourcePort = sourceNode.outputs.find((p) => p.id === connection.sourcePortId);
		const targetPort = targetNode.inputs.find((p) => p.id === connection.targetPortId);

		if (!sourcePort || !targetPort) return '';

		const start = getPortPosition(sourceNode, sourcePort, true);
		const end = getPortPosition(targetNode, targetPort, false);

		return calculateConnectionPath(start.x, start.y, end.x, end.y);
	}

	function getDraftConnectionPath(): string {
		if (
			!connectionState.isConnecting ||
			!connectionState.sourceNodeId ||
			!connectionState.sourcePortId
		) {
			return '';
		}

		const sourceNode = nodes.find((n) => n.id === connectionState.sourceNodeId);
		if (!sourceNode) return '';

		const sourcePort = sourceNode.outputs.find(
			(p) => p.id === connectionState.sourcePortId
		);
		if (!sourcePort) return '';

		const start = getPortPosition(sourceNode, sourcePort, true);
		return calculateConnectionPath(
			start.x,
			start.y,
			connectionState.mouseX,
			connectionState.mouseY
		);
	}

	let resizeObserver: ResizeObserver | null = null;

	onMount(() => {
		if (container) {
			width = container.clientWidth;
			height = container.clientHeight;

			resizeObserver = new ResizeObserver(() => {
				width = container.clientWidth;
				height = container.clientHeight;
			});
			resizeObserver.observe(container);
		}
	});

	onDestroy(() => {
		resizeObserver?.disconnect();
	});
</script>

<svelte:window on:keydown={handleKeyDown} />

<div
	bind:this={container}
	class="workflow-canvas"
	on:mousedown={handleMouseDown}
	on:mousemove={handleMouseMove}
	on:mouseup={handleMouseUp}
	on:wheel={handleWheel}
	role="application"
	aria-label="Workflow canvas"
	tabindex="0"
>
	<svg
		bind:this={svg}
		{width}
		{height}
		{viewBox}
		class="workflow-canvas__svg"
		on:click={handleCanvasClick}
	>
		<!-- Grid pattern -->
		<defs>
			<pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
				<path
					d="M 20 0 L 0 0 0 20"
					fill="none"
					stroke="var(--color-border-light)"
					stroke-width="0.5"
				/>
			</pattern>
		</defs>
		<rect width="100%" height="100%" fill="url(#grid)" />

		<!-- Connections -->
		<g class="workflow-canvas__connections">
			{#each connections as connection (connection.id)}
				<path
					d={getConnectionPath(connection)}
					fill="none"
					stroke="var(--color-border)"
					stroke-width="2"
					class="workflow-canvas__connection"
					class:workflow-canvas__connection--selected={false}
					on:click={(e) => handleConnectionClick(e, connection.id)}
				/>
			{/each}

			<!-- Draft connection -->
			{#if connectionState.isConnecting}
				<path
					d={getDraftConnectionPath()}
					fill="none"
					stroke="var(--color-primary)"
					stroke-width="2"
					stroke-dasharray="5,5"
					class="workflow-canvas__connection workflow-canvas__connection--draft"
				/>
			{/if}
		</g>

		<!-- Nodes -->
		<g class="workflow-canvas__nodes">
			{#each nodes as node (node.id)}
				{@const definition = NODE_DEFINITIONS[node.type]}
				<g
					class="workflow-canvas__node"
					class:workflow-canvas__node--selected={selectedNodeId === node.id}
					transform="translate({node.x}, {node.y})"
					on:mousedown={(e) => handleNodeMouseDown(e, node)}
					on:click={(e) => handleNodeClick(e, node)}
				>
					<!-- Node body -->
					<rect
						width={node.width}
						height={node.height}
						rx="8"
						fill="var(--color-bg)"
						stroke={selectedNodeId === node.id
							? 'var(--color-primary)'
							: 'var(--color-border)'}
						stroke-width={selectedNodeId === node.id ? 2 : 1}
					/>

					<!-- Header -->
					<rect
						width={node.width}
						height="36"
						rx="8"
						fill={NODE_COLOURS[definition.category]}
					/>
					<rect x="0" y="28" width={node.width} height="8" fill={NODE_COLOURS[definition.category]} />

					<!-- Title -->
					<text
						x="12"
						y="24"
						fill="white"
						font-size="12"
						font-weight="600"
						class="workflow-canvas__node-title"
					>
						{node.label}
					</text>

					<!-- Input ports -->
					{#each node.inputs as port, i}
						{@const portY = 48 + i * 24}
						<g
							class="workflow-canvas__port"
							on:mouseup={(e) => handlePortMouseUp(e, node, port, false)}
						>
							<circle
								cx="0"
								cy={portY}
								r="6"
								fill={PORT_COLOURS[port.type]}
								stroke="white"
								stroke-width="2"
							/>
							<text
								x="14"
								y={portY + 4}
								fill="var(--color-text-secondary)"
								font-size="10"
							>
								{port.name}
							</text>
						</g>
					{/each}

					<!-- Output ports -->
					{#each node.outputs as port, i}
						{@const portY = 48 + i * 24}
						<g
							class="workflow-canvas__port workflow-canvas__port--output"
							on:mousedown={(e) => handlePortMouseDown(e, node, port, true)}
						>
							<circle
								cx={node.width}
								cy={portY}
								r="6"
								fill={PORT_COLOURS[port.type]}
								stroke="white"
								stroke-width="2"
							/>
							<text
								x={node.width - 14}
								y={portY + 4}
								fill="var(--color-text-secondary)"
								font-size="10"
								text-anchor="end"
							>
								{port.name}
							</text>
						</g>
					{/each}
				</g>
			{/each}
		</g>
	</svg>

	<!-- Zoom indicator -->
	<div class="workflow-canvas__zoom">
		{Math.round(canvasState.zoom * 100)}%
	</div>
</div>

<style>
	.workflow-canvas {
		width: 100%;
		height: 100%;
		position: relative;
		overflow: hidden;
		background-color: var(--color-bg-secondary);
		border-radius: var(--radius-lg);
		cursor: grab;
	}

	.workflow-canvas:active {
		cursor: grabbing;
	}

	.workflow-canvas__svg {
		display: block;
	}

	.workflow-canvas__node {
		cursor: move;
	}

	.workflow-canvas__node-title {
		pointer-events: none;
		user-select: none;
	}

	.workflow-canvas__port {
		cursor: pointer;
	}

	.workflow-canvas__port:hover circle {
		r: 8;
	}

	.workflow-canvas__port--output {
		cursor: crosshair;
	}

	.workflow-canvas__connection {
		cursor: pointer;
		transition: stroke var(--transition-fast);
	}

	.workflow-canvas__connection:hover {
		stroke: var(--color-danger);
		stroke-width: 3;
	}

	.workflow-canvas__connection--draft {
		pointer-events: none;
	}

	.workflow-canvas__zoom {
		position: absolute;
		bottom: var(--space-3);
		right: var(--space-3);
		padding: var(--space-1) var(--space-2);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-muted);
	}
</style>
