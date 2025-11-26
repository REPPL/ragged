<!--
  Query Results Component
  ragged WebUI v0.7.3

  Displays query results with streaming support
-->
<script lang="ts">
	import type { Source } from '$types';
	import ResultCard from './ResultCard.svelte';
	import Skeleton from '../Skeleton.svelte';

	export let answer = '';
	export let sources: Source[] = [];
	export let loading = false;
	export let streaming = false;
	export let status = '';
	export let totalTime: number | null = null;
	export let error: string | null = null;

	$: hasResults = answer || sources.length > 0;
	$: showEmpty = !loading && !streaming && !hasResults && !error;
</script>

<div class="query-results">
	{#if error}
		<div class="query-results__error" role="alert">
			<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<circle cx="12" cy="12" r="10" />
				<path d="M12 8v4M12 16h.01" />
			</svg>
			<div>
				<p class="query-results__error-title">Something went wrong</p>
				<p class="query-results__error-message">{error}</p>
			</div>
		</div>
	{:else if loading || streaming}
		<div class="query-results__loading">
			{#if status}
				<p class="query-results__status">{status}</p>
			{/if}

			{#if streaming && answer}
				<div class="query-results__answer query-results__answer--streaming">
					<p>{answer}<span class="query-results__cursor">|</span></p>
				</div>
			{:else if loading}
				<div class="query-results__skeleton">
					<Skeleton height="24px" width="60%" />
					<Skeleton height="16px" width="100%" />
					<Skeleton height="16px" width="90%" />
					<Skeleton height="16px" width="75%" />
				</div>
			{/if}
		</div>
	{:else if hasResults}
		<div class="query-results__content">
			{#if answer}
				<div class="query-results__answer">
					<h3 class="query-results__heading">Answer</h3>
					<p class="query-results__text">{answer}</p>
				</div>
			{/if}

			{#if sources.length > 0}
				<div class="query-results__sources">
					<h3 class="query-results__heading">
						Sources
						<span class="query-results__count">({sources.length})</span>
					</h3>
					<div class="query-results__list">
						{#each sources as source, index (source.id)}
							<ResultCard {source} {index} />
						{/each}
					</div>
				</div>
			{/if}

			{#if totalTime !== null}
				<p class="query-results__time">
					Completed in {totalTime.toFixed(2)}s
				</p>
			{/if}
		</div>
	{:else if showEmpty}
		<div class="query-results__empty">
			<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
				<circle cx="11" cy="11" r="8" />
				<path d="M21 21l-4.35-4.35" />
			</svg>
			<h3>Search your documents</h3>
			<p>Enter a query above to search through your knowledge base</p>
		</div>
	{/if}
</div>

<style>
	.query-results {
		width: 100%;
		max-width: var(--content-max-width);
	}

	.query-results__error {
		display: flex;
		align-items: flex-start;
		gap: var(--space-4);
		padding: var(--space-4);
		background-color: var(--color-danger-light);
		border: 1px solid var(--color-danger);
		border-radius: var(--radius-lg);
		color: var(--color-danger);
	}

	.query-results__error-title {
		margin: 0;
		font-weight: var(--font-weight-semibold);
	}

	.query-results__error-message {
		margin: var(--space-1) 0 0;
		font-size: var(--font-size-sm);
		opacity: 0.9;
	}

	.query-results__loading {
		padding: var(--space-4);
	}

	.query-results__status {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
		margin-bottom: var(--space-4);
	}

	.query-results__skeleton {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.query-results__content {
		display: flex;
		flex-direction: column;
		gap: var(--space-6);
	}

	.query-results__answer {
		padding: var(--space-4);
		background-color: var(--color-bg-secondary);
		border-radius: var(--radius-lg);
	}

	.query-results__answer--streaming {
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
	}

	.query-results__heading {
		margin: 0 0 var(--space-3);
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
	}

	.query-results__count {
		font-weight: var(--font-weight-normal);
		color: var(--color-text-muted);
	}

	.query-results__text {
		margin: 0;
		font-size: var(--font-size-base);
		line-height: var(--line-height-relaxed);
		color: var(--color-text-secondary);
		white-space: pre-wrap;
	}

	.query-results__cursor {
		animation: blink 1s step-end infinite;
	}

	@keyframes blink {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0;
		}
	}

	.query-results__sources {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.query-results__list {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.query-results__time {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
		text-align: center;
	}

	.query-results__empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--space-12) var(--space-4);
		text-align: center;
		color: var(--color-text-muted);
	}

	.query-results__empty svg {
		margin-bottom: var(--space-4);
		opacity: 0.5;
	}

	.query-results__empty h3 {
		margin: 0 0 var(--space-2);
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-secondary);
	}

	.query-results__empty p {
		margin: 0;
		font-size: var(--font-size-base);
	}
</style>
