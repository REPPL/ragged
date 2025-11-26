<!--
  Collection Card Component
  ragged WebUI v0.7.3

  Displays a single collection with stats and actions
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { Collection } from '$types';
	import Badge from '../Badge.svelte';

	export let collection: Collection;
	export let selected = false;

	const dispatch = createEventDispatcher<{
		select: { collection: Collection };
		edit: { collection: Collection };
		delete: { collection: Collection };
	}>();

	function formatDate(dateString: string): string {
		const date = new Date(dateString);
		return date.toLocaleDateString('en-GB', {
			day: 'numeric',
			month: 'short',
			year: 'numeric'
		});
	}

	function getCollectionColour(name: string): string {
		// Generate a consistent colour based on collection name
		const colours = [
			'#4c6ef5', // primary
			'#40c057', // success
			'#fab005', // warning
			'#7950f2', // purple
			'#15aabf', // cyan
			'#e64980', // pink
			'#fd7e14'  // orange
		];
		const hash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
		return colours[hash % colours.length];
	}

	$: colour = getCollectionColour(collection.name);
</script>

<article
	class="collection-card"
	class:collection-card--selected={selected}
	role="article"
	aria-label="Collection: {collection.name}"
	style="--collection-colour: {colour}"
>
	<div class="collection-card__indicator" />

	<div class="collection-card__content">
		<div class="collection-card__header">
			<h3 class="collection-card__title">{collection.name}</h3>
			{#if collection.is_default}
				<Badge variant="primary" size="sm">Default</Badge>
			{/if}
		</div>

		{#if collection.description}
			<p class="collection-card__description">{collection.description}</p>
		{/if}

		<div class="collection-card__stats">
			<div class="collection-card__stat">
				<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
					<polyline points="14 2 14 8 20 8" />
				</svg>
				<span>{collection.document_count} documents</span>
			</div>
			<div class="collection-card__stat">
				<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<rect x="3" y="3" width="7" height="7" />
					<rect x="14" y="3" width="7" height="7" />
					<rect x="14" y="14" width="7" height="7" />
					<rect x="3" y="14" width="7" height="7" />
				</svg>
				<span>{collection.chunk_count} chunks</span>
			</div>
		</div>

		<p class="collection-card__date">
			Created {formatDate(collection.created_at)}
		</p>
	</div>

	<div class="collection-card__actions">
		<button
			type="button"
			class="collection-card__action"
			on:click|stopPropagation={() => dispatch('select', { collection })}
			aria-label="Select collection"
		>
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<circle cx="11" cy="11" r="8" />
				<path d="M21 21l-4.35-4.35" />
			</svg>
		</button>
		<button
			type="button"
			class="collection-card__action"
			on:click|stopPropagation={() => dispatch('edit', { collection })}
			aria-label="Edit collection"
		>
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
				<path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
			</svg>
		</button>
		{#if !collection.is_default}
			<button
				type="button"
				class="collection-card__action collection-card__action--danger"
				on:click|stopPropagation={() => dispatch('delete', { collection })}
				aria-label="Delete collection"
			>
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="3 6 5 6 21 6" />
					<path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
				</svg>
			</button>
		{/if}
	</div>
</article>

<style>
	.collection-card {
		display: flex;
		gap: var(--space-4);
		padding: var(--space-4);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
		transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
	}

	.collection-card:hover {
		border-color: var(--color-border-medium);
		box-shadow: var(--shadow-sm);
	}

	.collection-card--selected {
		border-color: var(--color-primary);
		background-color: var(--color-primary-light);
	}

	.collection-card__indicator {
		width: 4px;
		flex-shrink: 0;
		background-color: var(--collection-colour);
		border-radius: var(--radius-full);
	}

	.collection-card__content {
		flex: 1;
		min-width: 0;
	}

	.collection-card__header {
		display: flex;
		align-items: center;
		gap: var(--space-2);
	}

	.collection-card__title {
		margin: 0;
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.collection-card__description {
		margin: var(--space-2) 0 0;
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.collection-card__stats {
		display: flex;
		gap: var(--space-4);
		margin-top: var(--space-3);
	}

	.collection-card__stat {
		display: flex;
		align-items: center;
		gap: var(--space-1);
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.collection-card__stat svg {
		opacity: 0.7;
	}

	.collection-card__date {
		margin: var(--space-2) 0 0;
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.collection-card__actions {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
		flex-shrink: 0;
	}

	.collection-card__action {
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

	.collection-card__action:hover {
		color: var(--color-text-primary);
		background-color: var(--color-bg-secondary);
	}

	.collection-card__action--danger:hover {
		color: var(--color-danger);
		background-color: var(--color-danger-light);
	}
</style>
