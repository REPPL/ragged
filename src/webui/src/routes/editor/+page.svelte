<script lang="ts">
	/**
	 * Editor page - Block-based document editor.
	 *
	 * v0.9.1: Initial implementation
	 */

	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import BlockEditor from '$lib/components/editor/BlockEditor.svelte';
	import {
		editorStore,
		documentList,
		currentDocument,
		hasUnsavedChanges
	} from '$lib/stores/editor';

	let editor: BlockEditor;
	let showDocumentList = false;

	// Get document ID from URL query params
	$: documentId = $page.url.searchParams.get('id');

	onMount(() => {
		editorStore.init();

		// If no document ID, create a new one
		if (!documentId && $documentList.length === 0) {
			editorStore.createDocument('Untitled Document');
		}
	});

	function handleSave(event: CustomEvent<{ content: string; html: string }>) {
		// Document saved via editor
		console.log('Document saved');
	}

	function handleChange(event: CustomEvent<{ content: string }>) {
		// Content changed
	}

	function createNewDocument() {
		editorStore.createDocument('Untitled Document');
		showDocumentList = false;
	}

	function openDocument(id: string) {
		editorStore.loadDocument(id);
		showDocumentList = false;
	}

	function deleteDocument(id: string) {
		if (confirm('Are you sure you want to delete this document?')) {
			editorStore.deleteDocument(id);
		}
	}

	function exportMarkdown() {
		if (!$currentDocument) return;

		const markdown = editorStore.exportAsMarkdown($currentDocument.id);
		if (!markdown) return;

		const blob = new Blob([markdown], { type: 'text/markdown' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `${$currentDocument.title}.md`;
		a.click();
		URL.revokeObjectURL(url);
	}

	function formatDate(date: Date): string {
		return new Intl.DateTimeFormat('en-GB', {
			day: 'numeric',
			month: 'short',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		}).format(date);
	}
</script>

<svelte:head>
	<title>Editor - ragged</title>
</svelte:head>

<div class="editor-page">
	<!-- Sidebar -->
	<aside class="editor-sidebar" class:collapsed={!showDocumentList}>
		<div class="sidebar-header">
			<h2>Documents</h2>
			<button class="btn-icon" on:click={createNewDocument} title="New Document">
				<span>+</span>
			</button>
		</div>

		<div class="document-list">
			{#each $documentList as doc}
				<button
					class="document-item"
					class:active={$currentDocument?.id === doc.id}
					on:click={() => openDocument(doc.id)}
				>
					<div class="document-info">
						<span class="document-title">{doc.title}</span>
						<span class="document-date">{formatDate(doc.updatedAt)}</span>
					</div>
					<button
						class="btn-delete"
						on:click|stopPropagation={() => deleteDocument(doc.id)}
						title="Delete"
					>
						&times;
					</button>
				</button>
			{/each}

			{#if $documentList.length === 0}
				<div class="empty-state">
					<p>No documents yet</p>
					<button class="btn-primary" on:click={createNewDocument}> Create your first document </button>
				</div>
			{/if}
		</div>
	</aside>

	<!-- Main Editor Area -->
	<main class="editor-main">
		<header class="editor-header">
			<button class="btn-toggle-sidebar" on:click={() => (showDocumentList = !showDocumentList)}>
				<span class="hamburger">&#9776;</span>
			</button>

			{#if $currentDocument}
				<h1 class="document-title-header">{$currentDocument.title}</h1>

				{#if $hasUnsavedChanges}
					<span class="unsaved-badge">Unsaved</span>
				{/if}
			{/if}

			<div class="header-actions">
				<button class="btn-secondary" on:click={exportMarkdown} title="Export as Markdown">
					Export
				</button>
			</div>
		</header>

		<div class="editor-container">
			{#if $currentDocument}
				<BlockEditor
					bind:this={editor}
					documentId={$currentDocument.id}
					initialContent={$currentDocument.content}
					on:save={handleSave}
					on:change={handleChange}
				/>
			{:else}
				<div class="no-document">
					<p>Select a document or create a new one</p>
					<button class="btn-primary" on:click={createNewDocument}> Create New Document </button>
				</div>
			{/if}
		</div>
	</main>
</div>

<style>
	.editor-page {
		display: flex;
		height: 100vh;
		background: var(--color-background);
	}

	/* Sidebar */
	.editor-sidebar {
		width: 280px;
		background: var(--color-surface);
		border-right: 1px solid var(--color-border);
		display: flex;
		flex-direction: column;
		transition: width 0.2s ease, opacity 0.2s ease;
	}

	.editor-sidebar.collapsed {
		width: 0;
		overflow: hidden;
		opacity: 0;
	}

	.sidebar-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--space-3);
		border-bottom: 1px solid var(--color-border);
	}

	.sidebar-header h2 {
		font-size: 1rem;
		font-weight: 600;
		margin: 0;
	}

	.btn-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		border: none;
		border-radius: var(--radius-sm);
		background: var(--color-primary);
		color: white;
		cursor: pointer;
		font-size: 18px;
		font-weight: bold;
	}

	.btn-icon:hover {
		background: var(--color-primary-dark);
	}

	.document-list {
		flex: 1;
		overflow-y: auto;
		padding: var(--space-2);
	}

	.document-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		width: 100%;
		padding: var(--space-2) var(--space-3);
		border: none;
		border-radius: var(--radius-md);
		background: transparent;
		cursor: pointer;
		text-align: left;
		margin-bottom: var(--space-1);
		transition: background 0.15s ease;
	}

	.document-item:hover {
		background: var(--color-background-hover);
	}

	.document-item.active {
		background: var(--color-primary-light);
	}

	.document-info {
		display: flex;
		flex-direction: column;
		gap: 2px;
		overflow: hidden;
	}

	.document-title {
		font-weight: 500;
		color: var(--color-text);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.document-date {
		font-size: 12px;
		color: var(--color-text-secondary);
	}

	.btn-delete {
		opacity: 0;
		background: none;
		border: none;
		color: var(--color-error);
		cursor: pointer;
		font-size: 18px;
		padding: var(--space-1);
		transition: opacity 0.15s ease;
	}

	.document-item:hover .btn-delete {
		opacity: 1;
	}

	.empty-state {
		text-align: center;
		padding: var(--space-4);
		color: var(--color-text-secondary);
	}

	.empty-state p {
		margin-bottom: var(--space-3);
	}

	/* Main Editor */
	.editor-main {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-width: 0;
	}

	.editor-header {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		padding: var(--space-3) var(--space-4);
		border-bottom: 1px solid var(--color-border);
		background: var(--color-surface);
	}

	.btn-toggle-sidebar {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 36px;
		height: 36px;
		border: none;
		border-radius: var(--radius-sm);
		background: transparent;
		cursor: pointer;
		font-size: 20px;
		color: var(--color-text-secondary);
	}

	.btn-toggle-sidebar:hover {
		background: var(--color-background-hover);
	}

	.document-title-header {
		font-size: 1.125rem;
		font-weight: 600;
		margin: 0;
		flex: 1;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.unsaved-badge {
		padding: 2px 8px;
		background: var(--color-warning-light);
		color: var(--color-warning);
		border-radius: var(--radius-full);
		font-size: 12px;
		font-weight: 500;
	}

	.header-actions {
		display: flex;
		gap: var(--space-2);
	}

	.btn-secondary {
		padding: var(--space-2) var(--space-3);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		background: var(--color-surface);
		color: var(--color-text);
		cursor: pointer;
		font-size: 14px;
		transition: all 0.15s ease;
	}

	.btn-secondary:hover {
		background: var(--color-background-hover);
	}

	.btn-primary {
		padding: var(--space-2) var(--space-3);
		border: none;
		border-radius: var(--radius-md);
		background: var(--color-primary);
		color: white;
		cursor: pointer;
		font-size: 14px;
		transition: all 0.15s ease;
	}

	.btn-primary:hover {
		background: var(--color-primary-dark);
	}

	.editor-container {
		flex: 1;
		padding: var(--space-4);
		overflow: hidden;
	}

	.no-document {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		color: var(--color-text-secondary);
	}

	.no-document p {
		margin-bottom: var(--space-3);
	}

	/* Responsive */
	@media (max-width: 768px) {
		.editor-sidebar {
			position: fixed;
			left: 0;
			top: 0;
			bottom: 0;
			z-index: 100;
			box-shadow: var(--shadow-lg);
		}

		.editor-sidebar.collapsed {
			width: 0;
		}
	}
</style>
