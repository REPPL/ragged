<!--
  History Item Component
  ragged WebUI v0.7.3

  Individual query history item
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { QueryHistoryItem } from '$types';
	import Badge from '../Badge.svelte';

	export let item: QueryHistoryItem;

	const dispatch = createEventDispatcher<{
		rerun: { item: QueryHistoryItem };
		delete: { item: QueryHistoryItem };
		view: { item: QueryHistoryItem };
	}>();

	function formatDate(dateString: string): string {
		const date = new Date(dateString);
		const now = new Date();
		const diffMs = now.getTime() - date.getTime();
		const diffHours = diffMs / (1000 * 60 * 60);
		const diffDays = diffMs / (1000 * 60 * 60 * 24);

		if (diffHours < 1) {
			const mins = Math.floor(diffMs / (1000 * 60));
			return `${mins} minute${mins !== 1 ? 's' : ''} ago`;
		} else if (diffHours < 24) {
			const hours = Math.floor(diffHours);
			return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
		} else if (diffDays < 7) {
			const days = Math.floor(diffDays);
			return `${days} day${days !== 1 ? 's' : ''} ago`;
		} else {
			return date.toLocaleDateString('en-GB', {
				day: 'numeric',
				month: 'short',
				year: 'numeric'
			});
		}
	}

	function truncate(text: string, maxLength: number): string {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength).trim() + '...';
	}

	$: statusVariant =
		item.status === 'completed'
			? 'success'
			: item.status === 'failed'
				? 'danger'
				: 'secondary';
</script>

<article class="history-item" role="article" aria-label="Query: {truncate(item.query, 50)}">
	<div class="history-item__main" on:click={() => dispatch('view', { item })} on:keydown={(e) => e.key === 'Enter' && dispatch('view', { item })} role="button" tabindex="0">
		<div class="history-item__header">
			<Badge variant={statusVariant} size="sm">{item.status}</Badge>
			<span class="history-item__time">{formatDate(item.created_at)}</span>
		</div>

		<p class="history-item__query">{truncate(item.query, 150)}</p>

		{#if item.answer}
			<p class="history-item__answer">{truncate(item.answer, 200)}</p>
		{/if}

		<div class="history-item__meta">
			{#if item.source_count > 0}
				<span class="history-item__sources">
					{item.source_count} source{item.source_count !== 1 ? 's' : ''}
				</span>
			{/if}
			{#if item.duration}
				<span class="history-item__duration">{item.duration.toFixed(2)}s</span>
			{/if}
			{#if item.collection}
				<span class="history-item__collection">{item.collection}</span>
			{/if}
		</div>
	</div>

	<div class="history-item__actions">
		<button
			type="button"
			class="history-item__action"
			on:click|stopPropagation={() => dispatch('rerun', { item })}
			aria-label="Re-run query"
			title="Re-run query"
		>
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<polyline points="1 4 1 10 7 10" />
				<path d="M3.51 15a9 9 0 102.13-9.36L1 10" />
			</svg>
		</button>
		<button
			type="button"
			class="history-item__action history-item__action--danger"
			on:click|stopPropagation={() => dispatch('delete', { item })}
			aria-label="Delete from history"
			title="Delete"
		>
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<polyline points="3 6 5 6 21 6" />
				<path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
			</svg>
		</button>
	</div>
</article>

<style>
	.history-item {
		display: flex;
		gap: var(--space-4);
		padding: var(--space-4);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
		transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
	}

	.history-item:hover {
		border-color: var(--color-border-medium);
		box-shadow: var(--shadow-sm);
	}

	.history-item__main {
		flex: 1;
		min-width: 0;
		cursor: pointer;
	}

	.history-item__header {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		margin-bottom: var(--space-2);
	}

	.history-item__time {
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.history-item__query {
		margin: 0;
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-primary);
		line-height: var(--line-height-normal);
	}

	.history-item__answer {
		margin: var(--space-2) 0 0;
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		line-height: var(--line-height-relaxed);
	}

	.history-item__meta {
		display: flex;
		gap: var(--space-3);
		margin-top: var(--space-3);
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.history-item__meta > span {
		display: flex;
		align-items: center;
		gap: var(--space-1);
	}

	.history-item__meta > span::before {
		content: '';
		display: inline-block;
		width: 3px;
		height: 3px;
		border-radius: 50%;
		background-color: var(--color-border-medium);
	}

	.history-item__meta > span:first-child::before {
		display: none;
	}

	.history-item__actions {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
		flex-shrink: 0;
	}

	.history-item__action {
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

	.history-item__action:hover {
		color: var(--color-text-primary);
		background-color: var(--color-bg-secondary);
	}

	.history-item__action--danger:hover {
		color: var(--color-danger);
		background-color: var(--color-danger-light);
	}
</style>
