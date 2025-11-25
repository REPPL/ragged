<!--
  History Page
  ragged WebUI v0.7.3

  Query history interface
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import type { QueryHistoryItem } from '$types';
	import { addToast } from '$stores';
	import { api } from '$api';
	import { HistoryItem } from '$lib/components/history';
	import Modal from '$lib/components/Modal.svelte';
	import Button from '$lib/components/Button.svelte';
	import Input from '$lib/components/Input.svelte';
	import Select from '$lib/components/Select.svelte';
	import Skeleton from '$lib/components/Skeleton.svelte';

	let history: QueryHistoryItem[] = [];
	let loading = true;
	let error: string | null = null;

	// Filters
	let searchQuery = '';
	let statusFilter = 'all';
	let dateFilter = 'all';

	// Delete modal
	let showDeleteModal = false;
	let deletingItem: QueryHistoryItem | null = null;
	let deleting = false;

	// Clear all modal
	let showClearModal = false;
	let clearing = false;

	const statusOptions = [
		{ value: 'all', label: 'All statuses' },
		{ value: 'completed', label: 'Completed' },
		{ value: 'failed', label: 'Failed' }
	];

	const dateOptions = [
		{ value: 'all', label: 'All time' },
		{ value: 'today', label: 'Today' },
		{ value: 'week', label: 'This week' },
		{ value: 'month', label: 'This month' }
	];

	$: filteredHistory = history.filter((item) => {
		// Search filter
		if (searchQuery) {
			const query = searchQuery.toLowerCase();
			if (
				!item.query.toLowerCase().includes(query) &&
				!item.answer?.toLowerCase().includes(query)
			) {
				return false;
			}
		}
		// Status filter
		if (statusFilter !== 'all' && item.status !== statusFilter) {
			return false;
		}
		// Date filter
		if (dateFilter !== 'all') {
			const itemDate = new Date(item.created_at);
			const now = new Date();
			switch (dateFilter) {
				case 'today':
					if (itemDate.toDateString() !== now.toDateString()) return false;
					break;
				case 'week':
					const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
					if (itemDate < weekAgo) return false;
					break;
				case 'month':
					const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
					if (itemDate < monthAgo) return false;
					break;
			}
		}
		return true;
	});

	async function loadHistory() {
		loading = true;
		error = null;
		try {
			history = await api.history.list();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load history';
			addToast({
				type: 'error',
				title: 'Failed to load history',
				message: error
			});
		} finally {
			loading = false;
		}
	}

	function handleRerun(event: CustomEvent<{ item: QueryHistoryItem }>) {
		// Navigate to query page with the query pre-filled
		const params = new URLSearchParams({ q: event.detail.item.query });
		goto(`/?${params.toString()}`);
	}

	function handleView(event: CustomEvent<{ item: QueryHistoryItem }>) {
		// For now, just show the full query/answer in a toast
		// Later, this could open a detail modal
		addToast({
			type: 'info',
			title: 'Query details',
			message: event.detail.item.query
		});
	}

	function openDeleteModal(event: CustomEvent<{ item: QueryHistoryItem }>) {
		deletingItem = event.detail.item;
		showDeleteModal = true;
	}

	async function confirmDelete() {
		if (!deletingItem) return;
		deleting = true;
		try {
			await api.history.delete(deletingItem.id);
			addToast({
				type: 'success',
				title: 'Deleted',
				message: 'Query removed from history'
			});
			showDeleteModal = false;
			deletingItem = null;
			await loadHistory();
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to delete';
			addToast({
				type: 'error',
				title: 'Delete failed',
				message
			});
		} finally {
			deleting = false;
		}
	}

	async function confirmClearAll() {
		clearing = true;
		try {
			await api.history.clearAll();
			addToast({
				type: 'success',
				title: 'History cleared',
				message: 'All query history has been removed'
			});
			showClearModal = false;
			await loadHistory();
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to clear history';
			addToast({
				type: 'error',
				title: 'Clear failed',
				message
			});
		} finally {
			clearing = false;
		}
	}

	onMount(() => {
		loadHistory();
	});
</script>

<svelte:head>
	<title>History - ragged</title>
</svelte:head>

<div class="history-page">
	<div class="history-page__header">
		<div class="history-page__title-section">
			<h1 class="history-page__title">Query History</h1>
			<p class="history-page__subtitle">
				View and manage your past queries
			</p>
		</div>

		{#if history.length > 0}
			<Button variant="danger" on:click={() => (showClearModal = true)}>
				Clear all
			</Button>
		{/if}
	</div>

	<div class="history-page__toolbar">
		<div class="history-page__search">
			<Input
				bind:value={searchQuery}
				placeholder="Search history..."
				type="search"
				icon="search"
			/>
		</div>

		<div class="history-page__filters">
			<Select bind:value={statusFilter} options={statusOptions} label="Status" hideLabel />
			<Select bind:value={dateFilter} options={dateOptions} label="Date" hideLabel />
		</div>

		<Button variant="ghost" size="sm" on:click={loadHistory}>
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<polyline points="23 4 23 10 17 10" />
				<polyline points="1 20 1 14 7 14" />
				<path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
			</svg>
			Refresh
		</Button>
	</div>

	{#if error}
		<div class="history-page__error" role="alert">
			<p>{error}</p>
			<Button variant="primary" size="sm" on:click={loadHistory}>
				Try again
			</Button>
		</div>
	{:else if loading}
		<div class="history-page__loading">
			{#each Array(5) as _}
				<Skeleton height="120px" />
			{/each}
		</div>
	{:else if filteredHistory.length === 0}
		<div class="history-page__empty">
			{#if history.length === 0}
				<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<circle cx="12" cy="12" r="10" />
					<polyline points="12 6 12 12 16 14" />
				</svg>
				<h3>No history yet</h3>
				<p>Your query history will appear here</p>
				<Button variant="primary" on:click={() => goto('/')}>
					Make your first query
				</Button>
			{:else}
				<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<circle cx="11" cy="11" r="8" />
					<path d="M21 21l-4.35-4.35" />
				</svg>
				<h3>No results found</h3>
				<p>Try adjusting your search or filters</p>
			{/if}
		</div>
	{:else}
		<div class="history-page__list">
			{#each filteredHistory as item (item.id)}
				<HistoryItem
					{item}
					on:rerun={handleRerun}
					on:delete={openDeleteModal}
					on:view={handleView}
				/>
			{/each}
		</div>
	{/if}
</div>

<!-- Delete Modal -->
<Modal
	open={showDeleteModal}
	title="Delete Query"
	on:close={() => (showDeleteModal = false)}
>
	<p class="delete-modal__message">
		Are you sure you want to delete this query from your history?
	</p>

	<div class="delete-modal__actions" slot="footer">
		<Button variant="ghost" on:click={() => (showDeleteModal = false)}>
			Cancel
		</Button>
		<Button variant="danger" loading={deleting} on:click={confirmDelete}>
			Delete
		</Button>
	</div>
</Modal>

<!-- Clear All Modal -->
<Modal
	open={showClearModal}
	title="Clear All History"
	on:close={() => (showClearModal = false)}
>
	<p class="delete-modal__message">
		Are you sure you want to clear all query history? This action cannot be undone.
	</p>

	<div class="delete-modal__actions" slot="footer">
		<Button variant="ghost" on:click={() => (showClearModal = false)}>
			Cancel
		</Button>
		<Button variant="danger" loading={clearing} on:click={confirmClearAll}>
			Clear all
		</Button>
	</div>
</Modal>

<style>
	.history-page {
		display: flex;
		flex-direction: column;
		gap: var(--space-6);
		max-width: 900px;
		margin: 0 auto;
	}

	.history-page__header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: var(--space-4);
	}

	.history-page__title-section {
		flex: 1;
	}

	.history-page__title {
		margin: 0;
		font-size: var(--font-size-3xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-text-primary);
	}

	.history-page__subtitle {
		margin: var(--space-2) 0 0;
		font-size: var(--font-size-lg);
		color: var(--color-text-muted);
	}

	.history-page__toolbar {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: var(--space-4);
	}

	.history-page__search {
		flex: 1;
		min-width: 200px;
		max-width: 400px;
	}

	.history-page__filters {
		display: flex;
		gap: var(--space-3);
	}

	.history-page__error {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-4);
		padding: var(--space-8);
		text-align: center;
		color: var(--color-danger);
		background-color: var(--color-danger-light);
		border-radius: var(--radius-lg);
	}

	.history-page__loading {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.history-page__empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-4);
		padding: var(--space-12);
		text-align: center;
		color: var(--color-text-muted);
	}

	.history-page__empty svg {
		opacity: 0.5;
	}

	.history-page__empty h3 {
		margin: 0;
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-secondary);
	}

	.history-page__empty p {
		margin: 0;
	}

	.history-page__list {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.delete-modal__message {
		margin: 0;
		color: var(--color-text-secondary);
	}

	.delete-modal__actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--space-3);
	}

	@media (max-width: 640px) {
		.history-page__header {
			flex-direction: column;
			align-items: stretch;
		}

		.history-page__toolbar {
			flex-direction: column;
			align-items: stretch;
		}

		.history-page__search {
			max-width: none;
		}

		.history-page__filters {
			flex-wrap: wrap;
		}
	}
</style>
