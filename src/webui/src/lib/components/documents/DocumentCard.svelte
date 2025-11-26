<!--
  Document Card Component
  ragged WebUI v0.7.3

  Displays a single document with metadata and actions
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { Document } from '$types';
	import Badge from '../Badge.svelte';

	export let document: Document;
	export let selected = false;

	const dispatch = createEventDispatcher<{
		select: { document: Document };
		delete: { document: Document };
		view: { document: Document };
	}>();

	function getFileIcon(filename: string): string {
		const ext = filename.split('.').pop()?.toLowerCase();
		switch (ext) {
			case 'pdf':
				return '📄';
			case 'md':
			case 'markdown':
				return '📝';
			case 'txt':
				return '📃';
			case 'html':
				return '🌐';
			case 'py':
			case 'js':
			case 'ts':
				return '💻';
			case 'json':
				return '📋';
			case 'csv':
				return '📊';
			default:
				return '📁';
		}
	}

	function formatFileSize(bytes: number): string {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
	}

	function formatDate(dateString: string): string {
		const date = new Date(dateString);
		return date.toLocaleDateString('en-GB', {
			day: 'numeric',
			month: 'short',
			year: 'numeric'
		});
	}

	$: fileIcon = getFileIcon(document.filename);
	$: statusVariant =
		document.status === 'ready'
			? 'success'
			: document.status === 'processing'
				? 'warning'
				: document.status === 'error'
					? 'danger'
					: 'secondary';
</script>

<article
	class="document-card"
	class:document-card--selected={selected}
	role="article"
	aria-label="Document: {document.filename}"
>
	<div class="document-card__checkbox">
		<input
			type="checkbox"
			checked={selected}
			on:change={() => dispatch('select', { document })}
			aria-label="Select {document.filename}"
		/>
	</div>

	<div class="document-card__icon" aria-hidden="true">
		{fileIcon}
	</div>

	<div class="document-card__content">
		<div class="document-card__header">
			<h3 class="document-card__title">{document.filename}</h3>
			<Badge variant={statusVariant} size="sm">{document.status}</Badge>
		</div>

		<div class="document-card__meta">
			<span class="document-card__size">{formatFileSize(document.size)}</span>
			<span class="document-card__divider">•</span>
			<span class="document-card__chunks">{document.chunk_count} chunks</span>
			<span class="document-card__divider">•</span>
			<span class="document-card__date">{formatDate(document.created_at)}</span>
		</div>

		{#if document.collection}
			<div class="document-card__collection">
				<span class="document-card__collection-label">Collection:</span>
				<span class="document-card__collection-name">{document.collection}</span>
			</div>
		{/if}
	</div>

	<div class="document-card__actions">
		<button
			type="button"
			class="document-card__action"
			on:click={() => dispatch('view', { document })}
			aria-label="View document"
		>
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
				<circle cx="12" cy="12" r="3" />
			</svg>
		</button>
		<button
			type="button"
			class="document-card__action document-card__action--danger"
			on:click={() => dispatch('delete', { document })}
			aria-label="Delete document"
		>
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<polyline points="3 6 5 6 21 6" />
				<path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
			</svg>
		</button>
	</div>
</article>

<style>
	.document-card {
		display: flex;
		align-items: center;
		gap: var(--space-4);
		padding: var(--space-4);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
		transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
	}

	.document-card:hover {
		border-color: var(--color-border-medium);
		box-shadow: var(--shadow-sm);
	}

	.document-card--selected {
		border-color: var(--color-primary);
		background-color: var(--color-primary-light);
	}

	.document-card__checkbox input {
		width: 18px;
		height: 18px;
		cursor: pointer;
		accent-color: var(--color-primary);
	}

	.document-card__icon {
		font-size: var(--font-size-2xl);
		flex-shrink: 0;
	}

	.document-card__content {
		flex: 1;
		min-width: 0;
	}

	.document-card__header {
		display: flex;
		align-items: center;
		gap: var(--space-2);
	}

	.document-card__title {
		margin: 0;
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-primary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.document-card__meta {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		margin-top: var(--space-1);
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.document-card__divider {
		color: var(--color-border-medium);
	}

	.document-card__collection {
		margin-top: var(--space-2);
		font-size: var(--font-size-sm);
	}

	.document-card__collection-label {
		color: var(--color-text-muted);
	}

	.document-card__collection-name {
		color: var(--color-primary);
		font-weight: var(--font-weight-medium);
	}

	.document-card__actions {
		display: flex;
		gap: var(--space-2);
		flex-shrink: 0;
	}

	.document-card__action {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		padding: 0;
		color: var(--color-text-muted);
		background: none;
		border: none;
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: color var(--transition-fast), background-color var(--transition-fast);
	}

	.document-card__action:hover {
		color: var(--color-text-primary);
		background-color: var(--color-bg-secondary);
	}

	.document-card__action--danger:hover {
		color: var(--color-danger);
		background-color: var(--color-danger-light);
	}

	@media (max-width: 640px) {
		.document-card {
			flex-wrap: wrap;
		}

		.document-card__content {
			flex-basis: calc(100% - 100px);
		}

		.document-card__actions {
			margin-left: auto;
		}
	}
</style>
