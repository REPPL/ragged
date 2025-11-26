<!--
  Result Card Component
  ragged WebUI v0.7.3

  Individual query result card (from design specs)
-->
<script lang="ts">
	import type { Source } from '$types';
	import Badge from '../Badge.svelte';

	export let source: Source;
	export let expanded = false;
	export let index = 0;

	function toggleExpand() {
		expanded = !expanded;
	}

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
			default:
				return '📁';
		}
	}

	$: scorePercent = Math.round(source.score * 100);
	$: fileIcon = getFileIcon(source.filename);
</script>

<article
	class="result-card"
	class:result-card--expanded={expanded}
	role="article"
	aria-label="Search result {index + 1}: {source.filename}"
>
	<div class="result-card__header" on:click={toggleExpand} on:keydown={(e) => e.key === 'Enter' && toggleExpand()} role="button" tabindex="0">
		<Badge score={scorePercent} size="md" />

		<div class="result-card__meta">
			<div class="result-card__title">
				<span class="result-card__icon" aria-hidden="true">{fileIcon}</span>
				<span class="result-card__filename">{source.filename}</span>
			</div>
			<div class="result-card__info">
				<span class="result-card__chunk">Chunk {source.chunk_index + 1}</span>
				{#if source.page}
					<span class="result-card__divider">•</span>
					<span class="result-card__page">Page {source.page}</span>
				{/if}
			</div>
		</div>

		<button
			type="button"
			class="result-card__expand"
			aria-label={expanded ? 'Collapse' : 'Expand'}
			aria-expanded={expanded}
		>
			<svg
				width="20"
				height="20"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				class:rotated={expanded}
			>
				<polyline points="6 9 12 15 18 9" />
			</svg>
		</button>
	</div>

	<div class="result-card__content">
		<p class="result-card__excerpt">{source.excerpt}</p>
	</div>

	{#if expanded}
		<div class="result-card__actions">
			<button type="button" class="result-card__action">
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3" />
				</svg>
				Open document
			</button>
			<button type="button" class="result-card__action">
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
					<path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
				</svg>
				Copy excerpt
			</button>
		</div>
	{/if}
</article>

<style>
	.result-card {
		width: 100%;
		max-width: var(--card-result-max-width);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
		overflow: hidden;
		transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
	}

	.result-card:hover {
		border-color: var(--color-border-medium);
		box-shadow: var(--shadow-sm);
	}

	.result-card__header {
		display: flex;
		align-items: center;
		gap: var(--space-4);
		padding: var(--space-4);
		cursor: pointer;
	}

	.result-card__meta {
		flex: 1;
		min-width: 0;
	}

	.result-card__title {
		display: flex;
		align-items: center;
		gap: var(--space-2);
	}

	.result-card__icon {
		font-size: var(--font-size-lg);
	}

	.result-card__filename {
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-primary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.result-card__info {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		margin-top: var(--space-1);
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.result-card__divider {
		color: var(--color-border-medium);
	}

	.result-card__expand {
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

	.result-card__expand:hover {
		color: var(--color-text-primary);
		background-color: var(--color-bg-secondary);
	}

	.result-card__expand svg {
		transition: transform var(--transition-fast);
	}

	.result-card__expand svg.rotated {
		transform: rotate(180deg);
	}

	.result-card__content {
		padding: 0 var(--space-4) var(--space-4);
	}

	.result-card__excerpt {
		margin: 0;
		font-size: var(--font-size-sm);
		line-height: var(--line-height-relaxed);
		color: var(--color-text-secondary);
		display: -webkit-box;
		-webkit-line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.result-card--expanded .result-card__excerpt {
		-webkit-line-clamp: unset;
	}

	.result-card__actions {
		display: flex;
		gap: var(--space-2);
		padding: var(--space-3) var(--space-4);
		background-color: var(--color-bg-secondary);
		border-top: 1px solid var(--color-border-light);
	}

	.result-card__action {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-2) var(--space-3);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-secondary);
		background: none;
		border: none;
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: color var(--transition-fast), background-color var(--transition-fast);
	}

	.result-card__action:hover {
		color: var(--color-text-primary);
		background-color: var(--color-bg-tertiary);
	}
</style>
