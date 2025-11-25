<!--
  Query Page (Home)
  ragged WebUI v0.7.3

  Main query interface - the default landing page
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import type { Source, QueryMode, RetrievalMethod } from '$types';
	import { addToast } from '$stores';
	import { streamQuery } from '$api';
	import QueryInput from '$lib/components/query/QueryInput.svelte';
	import QueryOptions from '$lib/components/query/QueryOptions.svelte';
	import QueryResults from '$lib/components/query/QueryResults.svelte';

	let query = '';
	let answer = '';
	let sources: Source[] = [];
	let loading = false;
	let streaming = false;
	let status = '';
	let totalTime: number | null = null;
	let error: string | null = null;

	// Query options
	let mode: QueryMode = 'text';
	let topK = 5;
	let retrievalMethod: RetrievalMethod = 'hybrid';
	let showAdvanced = false;

	let abortFn: (() => void) | null = null;

	function handleSubmit(event: CustomEvent<{ query: string }>) {
		const queryText = event.detail.query;
		if (!queryText.trim()) return;

		// Reset state
		answer = '';
		sources = [];
		error = null;
		totalTime = null;
		loading = true;
		streaming = false;
		status = 'Connecting...';

		const startTime = performance.now();

		abortFn = streamQuery(
			{
				query: queryText,
				mode,
				top_k: topK,
				retrieval_method: retrievalMethod
			},
			{
				onStatus: (newStatus) => {
					status = newStatus;
					loading = false;
					streaming = true;
				},
				onToken: (token) => {
					answer += token;
				},
				onSources: (newSources) => {
					sources = newSources;
				},
				onComplete: (result) => {
					loading = false;
					streaming = false;
					totalTime = (performance.now() - startTime) / 1000;
					if (result.answer) {
						answer = result.answer;
					}
					if (result.sources) {
						sources = result.sources;
					}
					status = '';
				},
				onError: (err) => {
					loading = false;
					streaming = false;
					error = err.message;
					status = '';
					addToast({
						type: 'error',
						title: 'Query failed',
						message: err.message
					});
				}
			}
		);
	}

	function handleCancel() {
		if (abortFn) {
			abortFn();
			abortFn = null;
			loading = false;
			streaming = false;
			status = '';
			addToast({
				type: 'info',
				title: 'Query cancelled',
				message: 'The query was cancelled'
			});
		}
	}

	onMount(() => {
		// Focus the input on mount
		const input = document.querySelector('.query-input__textarea') as HTMLTextAreaElement;
		if (input) {
			input.focus();
		}

		return () => {
			// Cleanup on unmount
			if (abortFn) {
				abortFn();
			}
		};
	});
</script>

<svelte:head>
	<title>Query - ragged</title>
</svelte:head>

<div class="query-page">
	<div class="query-page__header">
		<h1 class="query-page__title">Search your documents</h1>
		<p class="query-page__subtitle">
			Ask questions about your knowledge base using natural language
		</p>
	</div>

	<div class="query-page__input-section">
		<QueryInput
			bind:value={query}
			loading={loading || streaming}
			disabled={false}
			on:submit={handleSubmit}
		/>

		<QueryOptions bind:mode bind:topK bind:retrievalMethod bind:showAdvanced />

		{#if loading || streaming}
			<button type="button" class="query-page__cancel" on:click={handleCancel}>
				Cancel query
			</button>
		{/if}
	</div>

	<div class="query-page__results-section">
		<QueryResults {answer} {sources} {loading} {streaming} {status} {totalTime} {error} />
	</div>
</div>

<style>
	.query-page {
		display: flex;
		flex-direction: column;
		gap: var(--space-8);
		max-width: var(--content-max-width);
		margin: 0 auto;
		padding: var(--space-4) 0;
	}

	.query-page__header {
		text-align: center;
	}

	.query-page__title {
		margin: 0;
		font-size: var(--font-size-3xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-text-primary);
	}

	.query-page__subtitle {
		margin: var(--space-2) 0 0;
		font-size: var(--font-size-lg);
		color: var(--color-text-muted);
	}

	.query-page__input-section {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
		align-items: center;
	}

	.query-page__cancel {
		padding: var(--space-2) var(--space-4);
		font-size: var(--font-size-sm);
		color: var(--color-danger);
		background: none;
		border: 1px solid var(--color-danger);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: background-color var(--transition-fast);
	}

	.query-page__cancel:hover {
		background-color: var(--color-danger-light);
	}

	.query-page__results-section {
		display: flex;
		justify-content: center;
	}

	@media (max-width: 640px) {
		.query-page__title {
			font-size: var(--font-size-2xl);
		}

		.query-page__subtitle {
			font-size: var(--font-size-base);
		}
	}
</style>
