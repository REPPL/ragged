<!--
  Collections Page
  ragged WebUI v0.7.3

  Collection management interface
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import type { Collection } from '$types';
	import { addToast } from '$stores';
	import { api } from '$api';
	import { CollectionCard, CollectionForm } from '$lib/components/collections';
	import Modal from '$lib/components/Modal.svelte';
	import Button from '$lib/components/Button.svelte';
	import Input from '$lib/components/Input.svelte';
	import Skeleton from '$lib/components/Skeleton.svelte';

	let collections: Collection[] = [];
	let loading = true;
	let error: string | null = null;

	// Search
	let searchQuery = '';

	// Create modal
	let showCreateModal = false;
	let creating = false;

	// Edit modal
	let showEditModal = false;
	let editingCollection: Collection | null = null;
	let editing = false;

	// Delete modal
	let showDeleteModal = false;
	let deletingCollection: Collection | null = null;
	let deleting = false;

	$: filteredCollections = collections.filter((c) =>
		c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
		c.description?.toLowerCase().includes(searchQuery.toLowerCase())
	);

	async function loadCollections() {
		loading = true;
		error = null;
		try {
			collections = await api.collections.list();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load collections';
			addToast({
				type: 'error',
				title: 'Failed to load collections',
				message: error
			});
		} finally {
			loading = false;
		}
	}

	async function handleCreate(event: CustomEvent<{ name: string; description: string }>) {
		creating = true;
		try {
			await api.collections.create(event.detail);
			addToast({
				type: 'success',
				title: 'Collection created',
				message: `Collection "${event.detail.name}" created successfully`
			});
			showCreateModal = false;
			await loadCollections();
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to create collection';
			addToast({
				type: 'error',
				title: 'Creation failed',
				message
			});
		} finally {
			creating = false;
		}
	}

	function openEditModal(event: CustomEvent<{ collection: Collection }>) {
		editingCollection = event.detail.collection;
		showEditModal = true;
	}

	async function handleEdit(event: CustomEvent<{ name: string; description: string }>) {
		if (!editingCollection) return;
		editing = true;
		try {
			await api.collections.update(editingCollection.id, event.detail);
			addToast({
				type: 'success',
				title: 'Collection updated',
				message: `Collection "${event.detail.name}" updated successfully`
			});
			showEditModal = false;
			editingCollection = null;
			await loadCollections();
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to update collection';
			addToast({
				type: 'error',
				title: 'Update failed',
				message
			});
		} finally {
			editing = false;
		}
	}

	function openDeleteModal(event: CustomEvent<{ collection: Collection }>) {
		deletingCollection = event.detail.collection;
		showDeleteModal = true;
	}

	async function confirmDelete() {
		if (!deletingCollection) return;
		deleting = true;
		try {
			await api.collections.delete(deletingCollection.id);
			addToast({
				type: 'success',
				title: 'Collection deleted',
				message: `Collection "${deletingCollection.name}" deleted`
			});
			showDeleteModal = false;
			deletingCollection = null;
			await loadCollections();
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to delete collection';
			addToast({
				type: 'error',
				title: 'Delete failed',
				message
			});
		} finally {
			deleting = false;
		}
	}

	function handleSelect(event: CustomEvent<{ collection: Collection }>) {
		// Navigate to query with this collection selected
		// For now, just show a toast
		addToast({
			type: 'info',
			title: 'Collection selected',
			message: `Searching in "${event.detail.collection.name}"`
		});
	}

	onMount(() => {
		loadCollections();
	});
</script>

<svelte:head>
	<title>Collections - ragged</title>
</svelte:head>

<div class="collections-page">
	<div class="collections-page__header">
		<div class="collections-page__title-section">
			<h1 class="collections-page__title">Collections</h1>
			<p class="collections-page__subtitle">
				Organise your documents into collections
			</p>
		</div>

		<Button variant="primary" on:click={() => (showCreateModal = true)}>
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<line x1="12" y1="5" x2="12" y2="19" />
				<line x1="5" y1="12" x2="19" y2="12" />
			</svg>
			New collection
		</Button>
	</div>

	<div class="collections-page__toolbar">
		<div class="collections-page__search">
			<Input
				bind:value={searchQuery}
				placeholder="Search collections..."
				type="search"
				icon="search"
			/>
		</div>

		<Button variant="ghost" size="sm" on:click={loadCollections}>
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<polyline points="23 4 23 10 17 10" />
				<polyline points="1 20 1 14 7 14" />
				<path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
			</svg>
			Refresh
		</Button>
	</div>

	{#if error}
		<div class="collections-page__error" role="alert">
			<p>{error}</p>
			<Button variant="primary" size="sm" on:click={loadCollections}>
				Try again
			</Button>
		</div>
	{:else if loading}
		<div class="collections-page__loading">
			{#each Array(4) as _}
				<Skeleton height="140px" />
			{/each}
		</div>
	{:else if filteredCollections.length === 0}
		<div class="collections-page__empty">
			{#if collections.length === 0}
				<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
				</svg>
				<h3>No collections yet</h3>
				<p>Create a collection to organise your documents</p>
				<Button variant="primary" on:click={() => (showCreateModal = true)}>
					Create your first collection
				</Button>
			{:else}
				<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<circle cx="11" cy="11" r="8" />
					<path d="M21 21l-4.35-4.35" />
				</svg>
				<h3>No results found</h3>
				<p>Try a different search term</p>
			{/if}
		</div>
	{:else}
		<div class="collections-page__grid">
			{#each filteredCollections as collection (collection.id)}
				<CollectionCard
					{collection}
					on:select={handleSelect}
					on:edit={openEditModal}
					on:delete={openDeleteModal}
				/>
			{/each}
		</div>
	{/if}
</div>

<!-- Create Modal -->
<Modal
	open={showCreateModal}
	title="Create Collection"
	on:close={() => (showCreateModal = false)}
>
	<CollectionForm
		loading={creating}
		on:submit={handleCreate}
		on:cancel={() => (showCreateModal = false)}
	/>
</Modal>

<!-- Edit Modal -->
<Modal
	open={showEditModal}
	title="Edit Collection"
	on:close={() => (showEditModal = false)}
>
	<CollectionForm
		collection={editingCollection}
		loading={editing}
		on:submit={handleEdit}
		on:cancel={() => (showEditModal = false)}
	/>
</Modal>

<!-- Delete Modal -->
<Modal
	open={showDeleteModal}
	title="Delete Collection"
	on:close={() => (showDeleteModal = false)}
>
	<p class="delete-modal__message">
		Are you sure you want to delete the collection "{deletingCollection?.name}"?
		{#if deletingCollection && deletingCollection.document_count > 0}
			<strong>This will also delete {deletingCollection.document_count} documents.</strong>
		{/if}
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

<style>
	.collections-page {
		display: flex;
		flex-direction: column;
		gap: var(--space-6);
		max-width: 1200px;
		margin: 0 auto;
	}

	.collections-page__header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: var(--space-4);
	}

	.collections-page__title-section {
		flex: 1;
	}

	.collections-page__title {
		margin: 0;
		font-size: var(--font-size-3xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-text-primary);
	}

	.collections-page__subtitle {
		margin: var(--space-2) 0 0;
		font-size: var(--font-size-lg);
		color: var(--color-text-muted);
	}

	.collections-page__toolbar {
		display: flex;
		align-items: center;
		gap: var(--space-4);
	}

	.collections-page__search {
		flex: 1;
		max-width: 400px;
	}

	.collections-page__error {
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

	.collections-page__loading {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: var(--space-4);
	}

	.collections-page__empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-4);
		padding: var(--space-12);
		text-align: center;
		color: var(--color-text-muted);
	}

	.collections-page__empty svg {
		opacity: 0.5;
	}

	.collections-page__empty h3 {
		margin: 0;
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-secondary);
	}

	.collections-page__empty p {
		margin: 0;
	}

	.collections-page__grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: var(--space-4);
	}

	.delete-modal__message {
		margin: 0;
		color: var(--color-text-secondary);
	}

	.delete-modal__message strong {
		display: block;
		margin-top: var(--space-2);
		color: var(--color-danger);
	}

	.delete-modal__actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--space-3);
	}

	@media (max-width: 640px) {
		.collections-page__header {
			flex-direction: column;
			align-items: stretch;
		}

		.collections-page__toolbar {
			flex-direction: column;
			align-items: stretch;
		}

		.collections-page__search {
			max-width: none;
		}
	}
</style>
