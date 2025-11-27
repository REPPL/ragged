<!--
  Documents Page
  ragged WebUI v0.9.2

  Advanced document management with faceted search and preview
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import type { Document, DocumentFilters, Collection } from '$types';
	import { addToast } from '$stores';
	import { api } from '$api';
	import {
		DocumentList,
		UploadZone,
		FilterPanel,
		PreviewPane
	} from '$lib/components/documents';
	import Modal from '$lib/components/Modal.svelte';
	import Button from '$lib/components/Button.svelte';

	let documents: Document[] = [];
	let collections: Collection[] = [];
	let availableTags: string[] = [];
	let loading = true;
	let error: string | null = null;
	let uploading = false;

	// Filter state
	let filters: DocumentFilters = {
		collection: null,
		tags: [],
		types: [],
		dateRange: null,
		search: ''
	};
	let filterPanelCollapsed = false;

	// Preview state
	let previewDocument: Document | null = null;

	// Modal state
	let showDeleteModal = false;
	let documentsToDelete: Document[] = [];
	let deleting = false;

	// Filtered documents
	$: filteredDocuments = documents.filter((doc) => {
		// Collection filter
		if (filters.collection && doc.collection !== filters.collection) {
			return false;
		}

		// Type filter
		if (filters.types.length > 0 && !filters.types.includes(doc.type)) {
			return false;
		}

		// Tag filter
		if (filters.tags.length > 0) {
			const docTags = doc.tags || [];
			if (!filters.tags.some((tag) => docTags.includes(tag))) {
				return false;
			}
		}

		// Date range filter
		if (filters.dateRange) {
			const docDate = new Date(doc.created_at);
			if (docDate < filters.dateRange.start || docDate > filters.dateRange.end) {
				return false;
			}
		}

		// Search filter (handled by DocumentList internally)
		return true;
	});

	// Extract unique tags from documents
	$: {
		const tagSet = new Set<string>();
		documents.forEach((doc) => {
			(doc.tags || []).forEach((tag) => tagSet.add(tag));
		});
		availableTags = Array.from(tagSet).sort();
	}

	async function loadDocuments() {
		loading = true;
		error = null;
		try {
			const [docs, cols] = await Promise.all([
				api.documents.list(),
				api.collections.list().catch(() => [])
			]);
			documents = docs;
			collections = cols;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load documents';
			addToast({
				type: 'error',
				title: 'Failed to load documents',
				message: error
			});
		} finally {
			loading = false;
		}
	}

	async function handleUpload(event: CustomEvent<{ files: File[] }>) {
		const { files } = event.detail;
		uploading = true;

		try {
			for (const file of files) {
				await api.documents.upload(file);
			}
			addToast({
				type: 'success',
				title: 'Upload complete',
				message: `${files.length} file(s) uploaded successfully`
			});
			await loadDocuments();
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Upload failed';
			addToast({
				type: 'error',
				title: 'Upload failed',
				message
			});
		} finally {
			uploading = false;
		}
	}

	function handleUploadError(event: CustomEvent<{ message: string }>) {
		addToast({
			type: 'warning',
			title: 'Upload warning',
			message: event.detail.message
		});
	}

	function handleDeleteRequest(event: CustomEvent<{ documents: Document[] }>) {
		documentsToDelete = event.detail.documents;
		showDeleteModal = true;
	}

	async function confirmDelete() {
		deleting = true;
		try {
			for (const doc of documentsToDelete) {
				await api.documents.delete(doc.id);
			}
			addToast({
				type: 'success',
				title: 'Documents deleted',
				message: `${documentsToDelete.length} document(s) deleted`
			});
			showDeleteModal = false;
			documentsToDelete = [];

			// Clear preview if deleted document was being viewed
			if (previewDocument && documentsToDelete.some((d) => d.id === previewDocument?.id)) {
				previewDocument = null;
			}

			await loadDocuments();
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Delete failed';
			addToast({
				type: 'error',
				title: 'Delete failed',
				message
			});
		} finally {
			deleting = false;
		}
	}

	function handleView(event: CustomEvent<{ document: Document }>) {
		previewDocument = event.detail.document;
	}

	function handleFilterChange(event: CustomEvent<DocumentFilters>) {
		filters = event.detail;
	}

	function handlePreviewDelete(event: CustomEvent<{ document: Document }>) {
		documentsToDelete = [event.detail.document];
		showDeleteModal = true;
	}

	onMount(() => {
		loadDocuments();
	});
</script>

<svelte:head>
	<title>Documents - ragged</title>
</svelte:head>

<div class="documents-page">
	<div class="documents-page__header">
		<div class="documents-page__header-content">
			<h1 class="documents-page__title">Documents</h1>
			<p class="documents-page__subtitle">
				Manage your knowledge base ({filteredDocuments.length} of {documents.length} documents)
			</p>
		</div>
		<div class="documents-page__upload-compact">
			<UploadZone
				disabled={uploading}
				compact
				on:upload={handleUpload}
				on:error={handleUploadError}
			/>
		</div>
	</div>

	<div class="documents-page__layout">
		<!-- Filter Panel -->
		<FilterPanel
			{filters}
			{collections}
			{availableTags}
			collapsed={filterPanelCollapsed}
			on:change={handleFilterChange}
		/>

		<!-- Document List -->
		<main class="documents-page__main">
			<DocumentList
				documents={filteredDocuments}
				{loading}
				{error}
				on:delete={handleDeleteRequest}
				on:view={handleView}
				on:refresh={loadDocuments}
			/>
		</main>

		<!-- Preview Pane -->
		<PreviewPane
			document={previewDocument}
			on:close={() => (previewDocument = null)}
			on:delete={handlePreviewDelete}
		/>
	</div>
</div>

<!-- Delete Confirmation Modal -->
<Modal
	open={showDeleteModal}
	title="Delete Documents"
	on:close={() => (showDeleteModal = false)}
>
	<p class="delete-modal__message">
		Are you sure you want to delete {documentsToDelete.length} document(s)?
		This action cannot be undone.
	</p>

	{#if documentsToDelete.length <= 5}
		<ul class="delete-modal__list">
			{#each documentsToDelete as doc}
				<li>{doc.filename}</li>
			{/each}
		</ul>
	{/if}

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
	.documents-page {
		display: flex;
		flex-direction: column;
		gap: var(--space-6);
		height: 100%;
		min-height: 0;
	}

	.documents-page__header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: var(--space-4);
		flex-wrap: wrap;
	}

	.documents-page__header-content {
		flex: 1;
		min-width: 200px;
	}

	.documents-page__title {
		margin: 0;
		font-size: var(--font-size-2xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-text-primary);
	}

	.documents-page__subtitle {
		margin: var(--space-1) 0 0;
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.documents-page__upload-compact {
		flex-shrink: 0;
	}

	.documents-page__layout {
		display: flex;
		gap: var(--space-6);
		flex: 1;
		min-height: 0;
	}

	.documents-page__main {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
	}

	.delete-modal__message {
		margin: 0 0 var(--space-4);
		color: var(--color-text-secondary);
	}

	.delete-modal__list {
		margin: 0;
		padding-left: var(--space-6);
		color: var(--color-text-muted);
		font-size: var(--font-size-sm);
	}

	.delete-modal__actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--space-3);
	}

	@media (max-width: 1280px) {
		.documents-page__layout {
			flex-wrap: wrap;
		}
	}

	@media (max-width: 768px) {
		.documents-page__header {
			flex-direction: column;
		}

		.documents-page__upload-compact {
			width: 100%;
		}
	}
</style>
