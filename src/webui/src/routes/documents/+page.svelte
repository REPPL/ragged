<!--
  Documents Page
  ragged WebUI v0.7.3

  Document management interface
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import type { Document } from '$types';
	import { addToast } from '$stores';
	import { api } from '$api';
	import { DocumentList, UploadZone } from '$lib/components/documents';
	import Modal from '$lib/components/Modal.svelte';
	import Button from '$lib/components/Button.svelte';

	let documents: Document[] = [];
	let loading = true;
	let error: string | null = null;
	let uploading = false;

	// Modal state
	let showDeleteModal = false;
	let documentsToDelete: Document[] = [];
	let deleting = false;

	// View modal
	let showViewModal = false;
	let viewingDocument: Document | null = null;

	async function loadDocuments() {
		loading = true;
		error = null;
		try {
			documents = await api.documents.list();
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
		viewingDocument = event.detail.document;
		showViewModal = true;
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
		<h1 class="documents-page__title">Documents</h1>
		<p class="documents-page__subtitle">
			Manage your knowledge base documents
		</p>
	</div>

	<div class="documents-page__upload">
		<UploadZone
			disabled={uploading}
			on:upload={handleUpload}
			on:error={handleUploadError}
		/>
	</div>

	<div class="documents-page__list">
		<DocumentList
			{documents}
			{loading}
			{error}
			on:delete={handleDeleteRequest}
			on:view={handleView}
			on:refresh={loadDocuments}
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

<!-- Document View Modal -->
<Modal
	open={showViewModal}
	title={viewingDocument?.filename ?? 'Document'}
	size="large"
	on:close={() => (showViewModal = false)}
>
	{#if viewingDocument}
		<div class="view-modal__content">
			<div class="view-modal__meta">
				<div class="view-modal__meta-item">
					<span class="view-modal__meta-label">Status:</span>
					<span class="view-modal__meta-value">{viewingDocument.status}</span>
				</div>
				<div class="view-modal__meta-item">
					<span class="view-modal__meta-label">Size:</span>
					<span class="view-modal__meta-value">
						{(viewingDocument.size / 1024).toFixed(1)} KB
					</span>
				</div>
				<div class="view-modal__meta-item">
					<span class="view-modal__meta-label">Chunks:</span>
					<span class="view-modal__meta-value">{viewingDocument.chunk_count}</span>
				</div>
				<div class="view-modal__meta-item">
					<span class="view-modal__meta-label">Created:</span>
					<span class="view-modal__meta-value">
						{new Date(viewingDocument.created_at).toLocaleString('en-GB')}
					</span>
				</div>
				{#if viewingDocument.collection}
					<div class="view-modal__meta-item">
						<span class="view-modal__meta-label">Collection:</span>
						<span class="view-modal__meta-value">{viewingDocument.collection}</span>
					</div>
				{/if}
			</div>
		</div>
	{/if}

	<div slot="footer">
		<Button variant="ghost" on:click={() => (showViewModal = false)}>
			Close
		</Button>
	</div>
</Modal>

<style>
	.documents-page {
		display: flex;
		flex-direction: column;
		gap: var(--space-8);
		max-width: 1200px;
		margin: 0 auto;
	}

	.documents-page__header {
		text-align: center;
	}

	.documents-page__title {
		margin: 0;
		font-size: var(--font-size-3xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-text-primary);
	}

	.documents-page__subtitle {
		margin: var(--space-2) 0 0;
		font-size: var(--font-size-lg);
		color: var(--color-text-muted);
	}

	.documents-page__upload {
		max-width: 600px;
		margin: 0 auto;
		width: 100%;
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

	.view-modal__content {
		min-height: 200px;
	}

	.view-modal__meta {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: var(--space-4);
	}

	.view-modal__meta-item {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.view-modal__meta-label {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.view-modal__meta-value {
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-primary);
	}
</style>
