<!--
  Workflows Page
  ragged WebUI v0.9.4

  Visual workflow editor for building RAG pipelines
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import type {
		Workflow,
		WorkflowNode,
		WorkflowConnection,
		NodeType,
		NodeConfig,
		CanvasState
	} from '$lib/workflow/types';
	import { createNode } from '$lib/workflow/nodes';
	import { removeNodeConnections, hasCycles } from '$lib/workflow/connections';
	import { WorkflowCanvas, NodePalette, NodeEditor } from '$lib/components/workflow';
	import Button from '$lib/components/Button.svelte';
	import { addToast } from '$stores';

	let workflow: Workflow = {
		id: 'new-workflow',
		name: 'Untitled Workflow',
		description: '',
		nodes: [],
		connections: [],
		createdAt: new Date().toISOString(),
		updatedAt: new Date().toISOString()
	};

	let selectedNodeId: string | null = null;
	let zoom = 1;
	let isModified = false;
	let isSaving = false;

	$: selectedNode = workflow.nodes.find((n) => n.id === selectedNodeId) || null;

	function handleNodeAdd(event: CustomEvent<{ type: NodeType; x: number; y: number }>) {
		const { type, x, y } = event.detail;
		const newNode = createNode(type, x, y);
		workflow.nodes = [...workflow.nodes, newNode];
		selectedNodeId = newNode.id;
		isModified = true;
	}

	function handleNodeSelect(event: CustomEvent<{ nodeId: string | null }>) {
		selectedNodeId = event.detail.nodeId;
	}

	function handleNodeMove(event: CustomEvent<{ nodeId: string; x: number; y: number }>) {
		const { nodeId, x, y } = event.detail;
		workflow.nodes = workflow.nodes.map((node) =>
			node.id === nodeId ? { ...node, x, y } : node
		);
		isModified = true;
	}

	function handleNodeDelete(event: CustomEvent<{ nodeId: string }>) {
		const { nodeId } = event.detail;
		workflow.nodes = workflow.nodes.filter((n) => n.id !== nodeId);
		workflow.connections = removeNodeConnections(workflow.connections, nodeId);
		if (selectedNodeId === nodeId) {
			selectedNodeId = null;
		}
		isModified = true;
	}

	function handleConnectionCreate(event: CustomEvent<{ connection: WorkflowConnection }>) {
		const { connection } = event.detail;

		// Check for cycles
		const testConnections = [...workflow.connections, connection];
		if (hasCycles(workflow.nodes, testConnections)) {
			addToast({
				type: 'error',
				title: 'Invalid Connection',
				message: 'This connection would create a cycle in the workflow'
			});
			return;
		}

		workflow.connections = [...workflow.connections, connection];
		isModified = true;
	}

	function handleConnectionDelete(event: CustomEvent<{ connectionId: string }>) {
		workflow.connections = workflow.connections.filter(
			(c) => c.id !== event.detail.connectionId
		);
		isModified = true;
	}

	function handleConfigChange(event: CustomEvent<{ nodeId: string; config: NodeConfig }>) {
		const { nodeId, config } = event.detail;
		workflow.nodes = workflow.nodes.map((node) =>
			node.id === nodeId ? { ...node, config } : node
		);
		isModified = true;
	}

	function handleDuplicate(event: CustomEvent<{ nodeId: string }>) {
		const sourceNode = workflow.nodes.find((n) => n.id === event.detail.nodeId);
		if (!sourceNode) return;

		const newNode = createNode(sourceNode.type, sourceNode.x + 40, sourceNode.y + 40);
		newNode.config = { ...sourceNode.config };
		workflow.nodes = [...workflow.nodes, newNode];
		selectedNodeId = newNode.id;
		isModified = true;
	}

	function handleViewChange(event: CustomEvent<CanvasState>) {
		zoom = event.detail.zoom;
	}

	function handleCanvasDrop(event: DragEvent) {
		event.preventDefault();
		const type = event.dataTransfer?.getData('application/workflow-node') as NodeType;
		if (!type) return;

		const rect = (event.target as HTMLElement).getBoundingClientRect();
		const x = (event.clientX - rect.left) / zoom;
		const y = (event.clientY - rect.top) / zoom;

		const newNode = createNode(type, x, y);
		workflow.nodes = [...workflow.nodes, newNode];
		selectedNodeId = newNode.id;
		isModified = true;
	}

	function handleCanvasDragOver(event: DragEvent) {
		event.preventDefault();
		if (event.dataTransfer) {
			event.dataTransfer.dropEffect = 'copy';
		}
	}

	async function handleSave() {
		isSaving = true;
		try {
			// TODO: Implement actual save to backend
			await new Promise((resolve) => setTimeout(resolve, 500));
			workflow.updatedAt = new Date().toISOString();
			isModified = false;
			addToast({
				type: 'success',
				title: 'Workflow Saved',
				message: 'Your workflow has been saved successfully'
			});
		} catch (err) {
			addToast({
				type: 'error',
				title: 'Save Failed',
				message: 'Failed to save workflow'
			});
		} finally {
			isSaving = false;
		}
	}

	function handleRun() {
		if (workflow.nodes.length === 0) {
			addToast({
				type: 'warning',
				title: 'Empty Workflow',
				message: 'Add some nodes to run the workflow'
			});
			return;
		}

		// TODO: Implement workflow execution
		addToast({
			type: 'info',
			title: 'Run Workflow',
			message: 'Workflow execution coming soon'
		});
	}

	function handleClear() {
		if (workflow.nodes.length === 0) return;

		if (confirm('Are you sure you want to clear all nodes?')) {
			workflow.nodes = [];
			workflow.connections = [];
			selectedNodeId = null;
			isModified = true;
		}
	}

	function handleExport() {
		const data = JSON.stringify(workflow, null, 2);
		const blob = new Blob([data], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `${workflow.name.toLowerCase().replace(/\s+/g, '-')}.json`;
		a.click();
		URL.revokeObjectURL(url);
	}

	function handleImport() {
		const input = document.createElement('input');
		input.type = 'file';
		input.accept = '.json';
		input.onchange = async (e) => {
			const file = (e.target as HTMLInputElement).files?.[0];
			if (!file) return;

			try {
				const text = await file.text();
				const imported = JSON.parse(text) as Workflow;
				workflow = imported;
				selectedNodeId = null;
				isModified = false;
				addToast({
					type: 'success',
					title: 'Workflow Imported',
					message: 'Workflow loaded successfully'
				});
			} catch (err) {
				addToast({
					type: 'error',
					title: 'Import Failed',
					message: 'Invalid workflow file'
				});
			}
		};
		input.click();
	}

	onMount(() => {
		// Load saved workflow if exists
		// TODO: Implement workflow loading
	});
</script>

<svelte:head>
	<title>{workflow.name} - Workflows - ragged</title>
</svelte:head>

<div class="workflows-page">
	<div class="workflows-page__header">
		<div class="workflows-page__title-section">
			<h1 class="workflows-page__title">
				{workflow.name}
				{#if isModified}
					<span class="workflows-page__modified">*</span>
				{/if}
			</h1>
			<p class="workflows-page__subtitle">
				Build RAG pipelines visually with drag-and-drop nodes
			</p>
		</div>

		<div class="workflows-page__controls">
			<Button variant="ghost" size="sm" on:click={handleImport}>
				<svg
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
				>
					<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
				</svg>
				Import
			</Button>
			<Button variant="ghost" size="sm" on:click={handleExport}>
				<svg
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
				>
					<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" />
				</svg>
				Export
			</Button>
			<Button variant="ghost" size="sm" on:click={handleClear}>
				<svg
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
				>
					<polyline points="3 6 5 6 21 6" />
					<path
						d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"
					/>
				</svg>
				Clear
			</Button>
			<Button variant="secondary" size="sm" on:click={handleSave} disabled={!isModified || isSaving}>
				{#if isSaving}
					Saving...
				{:else}
					Save
				{/if}
			</Button>
			<Button variant="primary" size="sm" on:click={handleRun}>
				<svg
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
				>
					<polygon points="5 3 19 12 5 21 5 3" />
				</svg>
				Run
			</Button>
		</div>
	</div>

	<div class="workflows-page__content">
		<div class="workflows-page__sidebar workflows-page__sidebar--left">
			<NodePalette on:nodeAdd={handleNodeAdd} />
		</div>

		<div
			class="workflows-page__canvas"
			on:drop={handleCanvasDrop}
			on:dragover={handleCanvasDragOver}
		>
			<WorkflowCanvas
				nodes={workflow.nodes}
				connections={workflow.connections}
				{selectedNodeId}
				{zoom}
				on:nodeSelect={handleNodeSelect}
				on:nodeMove={handleNodeMove}
				on:nodeDelete={handleNodeDelete}
				on:connectionCreate={handleConnectionCreate}
				on:connectionDelete={handleConnectionDelete}
				on:viewChange={handleViewChange}
			/>

			<!-- Stats overlay -->
			<div class="workflows-page__stats">
				<span class="workflows-page__stat">
					<strong>{workflow.nodes.length}</strong> nodes
				</span>
				<span class="workflows-page__stat">
					<strong>{workflow.connections.length}</strong> connections
				</span>
			</div>
		</div>

		<div class="workflows-page__sidebar workflows-page__sidebar--right">
			<NodeEditor
				node={selectedNode}
				on:configChange={handleConfigChange}
				on:close={() => (selectedNodeId = null)}
				on:delete={handleNodeDelete}
				on:duplicate={handleDuplicate}
			/>
		</div>
	</div>
</div>

<style>
	.workflows-page {
		display: flex;
		flex-direction: column;
		height: 100%;
		min-height: calc(100vh - 120px);
	}

	.workflows-page__header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: var(--space-4);
		padding-bottom: var(--space-4);
		flex-wrap: wrap;
	}

	.workflows-page__title-section {
		flex: 1;
	}

	.workflows-page__title {
		margin: 0;
		font-size: var(--font-size-3xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-text-primary);
	}

	.workflows-page__modified {
		color: var(--color-warning);
	}

	.workflows-page__subtitle {
		margin: var(--space-2) 0 0;
		font-size: var(--font-size-lg);
		color: var(--color-text-muted);
	}

	.workflows-page__controls {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		flex-wrap: wrap;
	}

	.workflows-page__content {
		display: flex;
		gap: var(--space-4);
		flex: 1;
		min-height: 0;
	}

	.workflows-page__sidebar {
		flex-shrink: 0;
	}

	.workflows-page__sidebar--left {
		width: 240px;
	}

	.workflows-page__sidebar--right {
		width: 300px;
	}

	.workflows-page__canvas {
		flex: 1;
		position: relative;
		min-width: 0;
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
		overflow: hidden;
	}

	.workflows-page__stats {
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
		pointer-events: none;
	}

	.workflows-page__stat strong {
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
	}

	@media (max-width: 1200px) {
		.workflows-page__content {
			flex-wrap: wrap;
		}

		.workflows-page__sidebar--left {
			width: 100%;
			max-height: 200px;
			order: 2;
		}

		.workflows-page__sidebar--right {
			width: 100%;
			order: 3;
		}

		.workflows-page__canvas {
			width: 100%;
			min-height: 500px;
			order: 1;
		}
	}

	@media (max-width: 640px) {
		.workflows-page__header {
			flex-direction: column;
			align-items: stretch;
		}

		.workflows-page__controls {
			justify-content: flex-end;
		}
	}
</style>
