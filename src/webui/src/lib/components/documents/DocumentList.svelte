<!--
  Document List Component
  ragged WebUI v0.7.3

  Displays a list of documents with filtering and bulk actions
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { Document } from '$types';
	import DocumentCard from './DocumentCard.svelte';
	import Input from '../Input.svelte';
	import Select from '../Select.svelte';
	import Button from '../Button.svelte';
	import Skeleton from '../Skeleton.svelte';

	export let documents: Document[] = [];
	export let loading = false;
	export let error: string | null = null;

	const dispatch = createEventDispatcher<{
		delete: { documents: Document[] };
		view: { document: Document };
		refresh: void;
	}>();

	let searchQuery = '';
	let statusFilter = 'all';
	let sortBy = 'date-desc';
	let selectedIds: Set<string> = new Set();

	const statusOptions = [
		{ value: 'all', label: 'All statuses' },
		{ value: 'ready', label: 'Ready' },
		{ value: 'processing', label: 'Processing' },
		{ value: 'error', label: 'Error' }
	];

	const sortOptions = [
		{ value: 'date-desc', label: 'Newest first' },
		{ value: 'date-asc', label: 'Oldest first' },
		{ value: 'name-asc', label: 'Name A-Z' },
		{ value: 'name-desc', label: 'Name Z-A' },
		{ value: 'size-desc', label: 'Largest first' },
		{ value: 'size-asc', label: 'Smallest first' }
	];

	$: filteredDocuments = documents
		.filter((doc) => {
			// Search filter
			if (searchQuery) {
				const query = searchQuery.toLowerCase();
				if (!doc.filename.toLowerCase().includes(query)) {
					return false;
				}
			}
			// Status filter
			if (statusFilter !== 'all' && doc.status !== statusFilter) {
				return false;
			}
			return true;
		})
		.sort((a, b) => {
			switch (sortBy) {
				case 'date-desc':
					return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
				case 'date-asc':
					return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
				case 'name-asc':
					return a.filename.localeCompare(b.filename);
				case 'name-desc':
					return b.filename.localeCompare(a.filename);
				case 'size-desc':
					return b.size - a.size;
				case 'size-asc':
					return a.size - b.size;
				default:
					return 0;
			}
		});

	$: allSelected = filteredDocuments.length > 0 && selectedIds.size === filteredDocuments.length;
	$: someSelected = selectedIds.size > 0;
	$: selectedDocuments = documents.filter((doc) => selectedIds.has(doc.id));

	function toggleSelectAll() {
		if (allSelected) {
			selectedIds = new Set();
		} else {
			selectedIds = new Set(filteredDocuments.map((doc) => doc.id));
		}
	}

	function handleSelect(event: CustomEvent<{ document: Document }>) {
		const { document } = event.detail;
		if (selectedIds.has(document.id)) {
			selectedIds.delete(document.id);
			selectedIds = selectedIds;
		} else {
			selectedIds.add(document.id);
			selectedIds = selectedIds;
		}
	}

	function handleDelete(event: CustomEvent<{ document: Document }>) {
		dispatch('delete', { documents: [event.detail.document] });
	}

	function handleView(event: CustomEvent<{ document: Document }>) {
		dispatch('view', { document: event.detail.document });
	}

	function handleBulkDelete() {
		if (selectedDocuments.length > 0) {
			dispatch('delete', { documents: selectedDocuments });
			selectedIds = new Set();
		}
	}
</script>

<div class="document-list">
	<div class="document-list__toolbar">
		<div class="document-list__search">
			<Input
				bind:value={searchQuery}
				placeholder="Search documents..."
				type="search"
				icon="search"
			/>
		</div>

		<div class="document-list__filters">
			<Select bind:value={statusFilter} options={statusOptions} label="Status" hideLabel />
			<Select bind:value={sortBy} options={sortOptions} label="Sort by" hideLabel />
		</div>

		<div class="document-list__actions">
			<Button variant="ghost" size="sm" on:click={() => dispatch('refresh')}>
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="23 4 23 10 17 10" />
					<polyline points="1 20 1 14 7 14" />
					<path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
				</svg>
				Refresh
			</Button>
		</div>
	</div>

	{#if someSelected}
		<div class="document-list__bulk-actions">
			<span class="document-list__selection-count">
				{selectedIds.size} selected
			</span>
			<Button variant="danger" size="sm" on:click={handleBulkDelete}>
				Delete selected
			</Button>
			<Button variant="ghost" size="sm" on:click={() => (selectedIds = new Set())}>
				Clear selection
			</Button>
		</div>
	{/if}

	{#if error}
		<div class="document-list__error" role="alert">
			<p>{error}</p>
			<Button variant="primary" size="sm" on:click={() => dispatch('refresh')}>
				Try again
			</Button>
		</div>
	{:else if loading}
		<div class="document-list__loading">
			{#each Array(5) as _}
				<div class="document-list__skeleton">
					<Skeleton height="80px" />
				</div>
			{/each}
		</div>
	{:else if filteredDocuments.length === 0}
		<div class="document-list__empty">
			{#if documents.length === 0}
				<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
					<polyline points="14 2 14 8 20 8" />
				</svg>
				<h3>No documents yet</h3>
				<p>Upload documents to get started</p>
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
		<div class="document-list__header">
			<label class="document-list__select-all">
				<input
					type="checkbox"
					checked={allSelected}
					indeterminate={someSelected && !allSelected}
					on:change={toggleSelectAll}
				/>
				<span>Select all ({filteredDocuments.length})</span>
			</label>
		</div>

		<div class="document-list__items">
			{#each filteredDocuments as document (document.id)}
				<DocumentCard
					{document}
					selected={selectedIds.has(document.id)}
					on:select={handleSelect}
					on:delete={handleDelete}
					on:view={handleView}
				/>
			{/each}
		</div>
	{/if}
</div>

<style>
	.document-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
	}

	.document-list__toolbar {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-4);
		align-items: center;
	}

	.document-list__search {
		flex: 1;
		min-width: 200px;
		max-width: 400px;
	}

	.document-list__filters {
		display: flex;
		gap: var(--space-3);
	}

	.document-list__actions {
		margin-left: auto;
	}

	.document-list__bulk-actions {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		padding: var(--space-3);
		background-color: var(--color-primary-light);
		border-radius: var(--radius-lg);
	}

	.document-list__selection-count {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-primary);
	}

	.document-list__error {
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

	.document-list__loading {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.document-list__empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-4);
		padding: var(--space-12);
		text-align: center;
		color: var(--color-text-muted);
	}

	.document-list__empty svg {
		opacity: 0.5;
	}

	.document-list__empty h3 {
		margin: 0;
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-secondary);
	}

	.document-list__empty p {
		margin: 0;
	}

	.document-list__header {
		padding: var(--space-2) var(--space-4);
		background-color: var(--color-bg-secondary);
		border-radius: var(--radius-md);
	}

	.document-list__select-all {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		cursor: pointer;
	}

	.document-list__select-all input {
		width: 18px;
		height: 18px;
		accent-color: var(--color-primary);
	}

	.document-list__items {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	@media (max-width: 768px) {
		.document-list__toolbar {
			flex-direction: column;
			align-items: stretch;
		}

		.document-list__search {
			max-width: none;
		}

		.document-list__filters {
			flex-wrap: wrap;
		}

		.document-list__actions {
			margin-left: 0;
		}
	}
</style>
