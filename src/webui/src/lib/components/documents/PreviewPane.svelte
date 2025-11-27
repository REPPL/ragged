<!--
  Preview Pane Component
  ragged WebUI v0.9.2

  Document preview sidebar with metadata and chunks
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { Document } from '$types';
	import Button from '../Button.svelte';
	import Badge from '../Badge.svelte';

	export let document: Document | null = null;
	export let loading = false;

	const dispatch = createEventDispatcher<{
		close: void;
		delete: { document: Document };
		edit: { document: Document };
	}>();

	function formatFileSize(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString('en-GB', {
			day: 'numeric',
			month: 'short',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function getStatusVariant(status: string): 'success' | 'warning' | 'danger' | 'default' {
		switch (status) {
			case 'ready':
				return 'success';
			case 'processing':
				return 'warning';
			case 'error':
				return 'danger';
			default:
				return 'default';
		}
	}

	function getTypeIcon(type: string): string {
		const icons: Record<string, string> = {
			pdf: '📄',
			markdown: '📝',
			text: '📃',
			html: '🌐',
			code: '💻',
			unknown: '📎'
		};
		return icons[type] || icons.unknown;
	}
</script>

<aside class="preview-pane" class:preview-pane--open={document !== null}>
	{#if document}
		<div class="preview-pane__header">
			<div class="preview-pane__title-row">
				<span class="preview-pane__icon">{getTypeIcon(document.type)}</span>
				<h2 class="preview-pane__title">{document.filename}</h2>
			</div>
			<button
				type="button"
				class="preview-pane__close"
				on:click={() => dispatch('close')}
				aria-label="Close preview"
			>
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="18" y1="6" x2="6" y2="18" />
					<line x1="6" y1="6" x2="18" y2="18" />
				</svg>
			</button>
		</div>

		<div class="preview-pane__content">
			<!-- Status -->
			<div class="preview-pane__status">
				<Badge variant={getStatusVariant(document.status)}>
					{document.status}
				</Badge>
			</div>

			<!-- Metadata Grid -->
			<section class="preview-pane__section">
				<h3 class="preview-pane__section-title">Details</h3>
				<dl class="preview-pane__meta">
					<div class="preview-pane__meta-item">
						<dt>Size</dt>
						<dd>{formatFileSize(document.size)}</dd>
					</div>
					<div class="preview-pane__meta-item">
						<dt>Type</dt>
						<dd>{document.type}</dd>
					</div>
					<div class="preview-pane__meta-item">
						<dt>Chunks</dt>
						<dd>{document.chunk_count}</dd>
					</div>
					<div class="preview-pane__meta-item">
						<dt>Created</dt>
						<dd>{formatDate(document.created_at)}</dd>
					</div>
					{#if document.updated_at !== document.created_at}
						<div class="preview-pane__meta-item">
							<dt>Updated</dt>
							<dd>{formatDate(document.updated_at)}</dd>
						</div>
					{/if}
					{#if document.collection}
						<div class="preview-pane__meta-item">
							<dt>Collection</dt>
							<dd>{document.collection}</dd>
						</div>
					{/if}
				</dl>
			</section>

			<!-- Tags -->
			{#if document.tags && document.tags.length > 0}
				<section class="preview-pane__section">
					<h3 class="preview-pane__section-title">Tags</h3>
					<div class="preview-pane__tags">
						{#each document.tags as tag}
							<span class="preview-pane__tag">#{tag}</span>
						{/each}
					</div>
				</section>
			{/if}

			<!-- Extended Metadata -->
			{#if document.metadata}
				<section class="preview-pane__section">
					<h3 class="preview-pane__section-title">Metadata</h3>
					<dl class="preview-pane__meta">
						{#if document.metadata.title}
							<div class="preview-pane__meta-item preview-pane__meta-item--full">
								<dt>Title</dt>
								<dd>{document.metadata.title}</dd>
							</div>
						{/if}
						{#if document.metadata.author}
							<div class="preview-pane__meta-item">
								<dt>Author</dt>
								<dd>{document.metadata.author}</dd>
							</div>
						{/if}
						{#if document.metadata.pages}
							<div class="preview-pane__meta-item">
								<dt>Pages</dt>
								<dd>{document.metadata.pages}</dd>
							</div>
						{/if}
						{#if document.metadata.language}
							<div class="preview-pane__meta-item">
								<dt>Language</dt>
								<dd>{document.metadata.language}</dd>
							</div>
						{/if}
						{#if document.metadata.domain}
							<div class="preview-pane__meta-item">
								<dt>Domain</dt>
								<dd>{document.metadata.domain}</dd>
							</div>
						{/if}
					</dl>
				</section>
			{/if}
		</div>

		<div class="preview-pane__actions">
			<Button
				variant="danger"
				size="sm"
				on:click={() => dispatch('delete', { document })}
			>
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="3 6 5 6 21 6" />
					<path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
				</svg>
				Delete
			</Button>
		</div>
	{:else}
		<div class="preview-pane__empty">
			<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
				<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
				<polyline points="14 2 14 8 20 8" />
			</svg>
			<p>Select a document to preview</p>
		</div>
	{/if}
</aside>

<style>
	.preview-pane {
		display: flex;
		flex-direction: column;
		width: 360px;
		min-width: 360px;
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
		overflow: hidden;
	}

	.preview-pane__header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: var(--space-3);
		padding: var(--space-4);
		border-bottom: 1px solid var(--color-border-light);
		background-color: var(--color-bg-secondary);
	}

	.preview-pane__title-row {
		display: flex;
		align-items: flex-start;
		gap: var(--space-2);
		flex: 1;
		min-width: 0;
	}

	.preview-pane__icon {
		font-size: var(--font-size-xl);
		flex-shrink: 0;
	}

	.preview-pane__title {
		margin: 0;
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
		word-break: break-word;
	}

	.preview-pane__close {
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

	.preview-pane__close:hover {
		color: var(--color-text-primary);
		background-color: var(--color-bg-tertiary);
	}

	.preview-pane__content {
		flex: 1;
		overflow-y: auto;
		padding: var(--space-4);
	}

	.preview-pane__status {
		margin-bottom: var(--space-4);
	}

	.preview-pane__section {
		margin-bottom: var(--space-5);
	}

	.preview-pane__section:last-child {
		margin-bottom: 0;
	}

	.preview-pane__section-title {
		margin: 0 0 var(--space-3);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.preview-pane__meta {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--space-3);
		margin: 0;
	}

	.preview-pane__meta-item {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.preview-pane__meta-item--full {
		grid-column: 1 / -1;
	}

	.preview-pane__meta-item dt {
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.preview-pane__meta-item dd {
		margin: 0;
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-primary);
	}

	.preview-pane__tags {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-2);
	}

	.preview-pane__tag {
		padding: var(--space-1) var(--space-2);
		font-size: var(--font-size-xs);
		color: var(--color-primary);
		background-color: var(--color-primary-light);
		border-radius: var(--radius-full);
	}

	.preview-pane__actions {
		display: flex;
		gap: var(--space-2);
		padding: var(--space-4);
		border-top: 1px solid var(--color-border-light);
		background-color: var(--color-bg-secondary);
	}

	.preview-pane__empty {
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

	.preview-pane__empty svg {
		opacity: 0.5;
	}

	@media (max-width: 1280px) {
		.preview-pane {
			position: fixed;
			top: 0;
			right: 0;
			bottom: 0;
			z-index: var(--z-modal);
			border-radius: 0;
			transform: translateX(100%);
			transition: transform var(--transition-normal);
		}

		.preview-pane--open {
			transform: translateX(0);
		}
	}
</style>
