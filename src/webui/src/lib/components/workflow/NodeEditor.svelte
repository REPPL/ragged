<!--
  Node Editor Component
  ragged WebUI v0.9.4

  Configuration panel for selected workflow node
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { WorkflowNode, NodeConfig, ConfigField } from '$lib/workflow/types';
	import { NODE_COLOURS } from '$lib/workflow/types';
	import { NODE_DEFINITIONS } from '$lib/workflow/nodes';
	import Button from '../Button.svelte';

	export let node: WorkflowNode | null = null;

	const dispatch = createEventDispatcher<{
		configChange: { nodeId: string; config: NodeConfig };
		close: void;
		delete: { nodeId: string };
		duplicate: { nodeId: string };
	}>();

	$: definition = node ? NODE_DEFINITIONS[node.type] : null;
	$: configSchema = definition?.configSchema || [];

	function handleFieldChange(key: string, value: unknown) {
		if (!node) return;
		const newConfig = { ...node.config, [key]: value };
		dispatch('configChange', { nodeId: node.id, config: newConfig });
	}

	function handleTextInput(event: Event, field: ConfigField) {
		const target = event.target as HTMLInputElement;
		handleFieldChange(field.key, target.value);
	}

	function handleNumberInput(event: Event, field: ConfigField) {
		const target = event.target as HTMLInputElement;
		handleFieldChange(field.key, parseFloat(target.value) || 0);
	}

	function handleSelectChange(event: Event, field: ConfigField) {
		const target = event.target as HTMLSelectElement;
		handleFieldChange(field.key, target.value);
	}

	function handleCheckboxChange(event: Event, field: ConfigField) {
		const target = event.target as HTMLInputElement;
		handleFieldChange(field.key, target.checked);
	}

	function handleTextareaInput(event: Event, field: ConfigField) {
		const target = event.target as HTMLTextAreaElement;
		handleFieldChange(field.key, target.value);
	}
</script>

<aside class="node-editor" class:node-editor--open={node !== null}>
	{#if node && definition}
		<div class="node-editor__header">
			<div class="node-editor__title-row">
				<span
					class="node-editor__type-badge"
					style="background-color: {NODE_COLOURS[definition.category]}"
				>
					{definition.category}
				</span>
				<h3 class="node-editor__title">{node.label}</h3>
			</div>
			<button
				type="button"
				class="node-editor__close"
				on:click={() => dispatch('close')}
				aria-label="Close editor"
			>
				<svg
					width="20"
					height="20"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
				>
					<line x1="18" y1="6" x2="6" y2="18" />
					<line x1="6" y1="6" x2="18" y2="18" />
				</svg>
			</button>
		</div>

		<div class="node-editor__content">
			<p class="node-editor__description">{definition.description}</p>

			{#if configSchema.length > 0}
				<form class="node-editor__form" on:submit|preventDefault>
					{#each configSchema as field}
						<div class="node-editor__field">
							<label class="node-editor__label" for={`field-${field.key}`}>
								{field.label}
								{#if field.required}
									<span class="node-editor__required">*</span>
								{/if}
							</label>

							{#if field.type === 'text'}
								<input
									id={`field-${field.key}`}
									type="text"
									value={node.config[field.key] ?? field.default ?? ''}
									placeholder={field.placeholder}
									class="node-editor__input"
									on:input={(e) => handleTextInput(e, field)}
								/>
							{:else if field.type === 'number'}
								<input
									id={`field-${field.key}`}
									type="number"
									value={node.config[field.key] ?? field.default ?? 0}
									placeholder={field.placeholder}
									class="node-editor__input"
									on:input={(e) => handleNumberInput(e, field)}
								/>
							{:else if field.type === 'select'}
								<select
									id={`field-${field.key}`}
									value={node.config[field.key] ?? field.default ?? ''}
									class="node-editor__select"
									on:change={(e) => handleSelectChange(e, field)}
								>
									{#each field.options || [] as option}
										<option value={option.value}>{option.label}</option>
									{/each}
								</select>
							{:else if field.type === 'boolean'}
								<label class="node-editor__checkbox">
									<input
										id={`field-${field.key}`}
										type="checkbox"
										checked={node.config[field.key] ?? field.default ?? false}
										on:change={(e) => handleCheckboxChange(e, field)}
									/>
									<span>Enabled</span>
								</label>
							{:else if field.type === 'textarea'}
								<textarea
									id={`field-${field.key}`}
									value={node.config[field.key] ?? field.default ?? ''}
									placeholder={field.placeholder}
									class="node-editor__textarea"
									rows="4"
									on:input={(e) => handleTextareaInput(e, field)}
								/>
							{/if}
						</div>
					{/each}
				</form>
			{:else}
				<div class="node-editor__no-config">
					<p>This node has no configurable options.</p>
				</div>
			{/if}

			<!-- Port info -->
			<div class="node-editor__ports">
				{#if node.inputs.length > 0}
					<div class="node-editor__port-section">
						<h4 class="node-editor__port-title">Inputs</h4>
						<ul class="node-editor__port-list">
							{#each node.inputs as port}
								<li class="node-editor__port">
									<span class="node-editor__port-name">{port.name}</span>
									<span class="node-editor__port-type">{port.type}</span>
								</li>
							{/each}
						</ul>
					</div>
				{/if}

				{#if node.outputs.length > 0}
					<div class="node-editor__port-section">
						<h4 class="node-editor__port-title">Outputs</h4>
						<ul class="node-editor__port-list">
							{#each node.outputs as port}
								<li class="node-editor__port">
									<span class="node-editor__port-name">{port.name}</span>
									<span class="node-editor__port-type">{port.type}</span>
								</li>
							{/each}
						</ul>
					</div>
				{/if}
			</div>
		</div>

		<div class="node-editor__actions">
			<Button
				variant="ghost"
				size="sm"
				on:click={() => dispatch('duplicate', { nodeId: node.id })}
			>
				<svg
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
				>
					<rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
					<path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
				</svg>
				Duplicate
			</Button>
			<Button
				variant="ghost"
				size="sm"
				on:click={() => dispatch('delete', { nodeId: node.id })}
			>
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
				Delete
			</Button>
		</div>
	{:else}
		<div class="node-editor__empty">
			<svg
				width="48"
				height="48"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="1.5"
			>
				<rect x="3" y="3" width="18" height="18" rx="2" />
				<line x1="9" y1="3" x2="9" y2="21" />
			</svg>
			<p>Select a node to edit its configuration</p>
		</div>
	{/if}
</aside>

<style>
	.node-editor {
		display: flex;
		flex-direction: column;
		width: 300px;
		min-width: 300px;
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
		overflow: hidden;
	}

	.node-editor__header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: var(--space-3);
		padding: var(--space-4);
		border-bottom: 1px solid var(--color-border-light);
		background-color: var(--color-bg-secondary);
	}

	.node-editor__title-row {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	.node-editor__type-badge {
		display: inline-block;
		padding: var(--space-1) var(--space-2);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		color: white;
		border-radius: var(--radius-full);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		width: fit-content;
	}

	.node-editor__title {
		margin: 0;
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
	}

	.node-editor__close {
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

	.node-editor__close:hover {
		color: var(--color-text-primary);
		background-color: var(--color-bg-tertiary);
	}

	.node-editor__content {
		flex: 1;
		overflow-y: auto;
		padding: var(--space-4);
	}

	.node-editor__description {
		margin: 0 0 var(--space-4);
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.node-editor__form {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
	}

	.node-editor__field {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.node-editor__label {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-secondary);
	}

	.node-editor__required {
		color: var(--color-danger);
	}

	.node-editor__input,
	.node-editor__select,
	.node-editor__textarea {
		padding: var(--space-2);
		font-size: var(--font-size-sm);
		color: var(--color-text-primary);
		background-color: var(--color-bg-secondary);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		outline: none;
		transition: border-color var(--transition-fast);
	}

	.node-editor__input:focus,
	.node-editor__select:focus,
	.node-editor__textarea:focus {
		border-color: var(--color-primary);
	}

	.node-editor__textarea {
		resize: vertical;
		min-height: 80px;
		font-family: var(--font-mono);
	}

	.node-editor__checkbox {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		cursor: pointer;
	}

	.node-editor__checkbox input {
		width: 16px;
		height: 16px;
		accent-color: var(--color-primary);
	}

	.node-editor__no-config {
		padding: var(--space-4);
		text-align: center;
		color: var(--color-text-muted);
		font-size: var(--font-size-sm);
	}

	.node-editor__ports {
		margin-top: var(--space-4);
		padding-top: var(--space-4);
		border-top: 1px solid var(--color-border-light);
	}

	.node-editor__port-section {
		margin-bottom: var(--space-3);
	}

	.node-editor__port-title {
		margin: 0 0 var(--space-2);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.node-editor__port-list {
		list-style: none;
		margin: 0;
		padding: 0;
	}

	.node-editor__port {
		display: flex;
		justify-content: space-between;
		padding: var(--space-1) 0;
		font-size: var(--font-size-sm);
	}

	.node-editor__port-name {
		color: var(--color-text-secondary);
	}

	.node-editor__port-type {
		color: var(--color-text-muted);
		font-family: var(--font-mono);
		font-size: var(--font-size-xs);
	}

	.node-editor__actions {
		display: flex;
		gap: var(--space-2);
		padding: var(--space-3);
		border-top: 1px solid var(--color-border-light);
	}

	.node-editor__empty {
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

	.node-editor__empty svg {
		opacity: 0.5;
	}
</style>
