<!--
  Sidebar Component
  ragged WebUI v0.7.3

  Document library sidebar (320px width from design)
-->
<script lang="ts">
	import { sidebar, isSidebarOpen, sidebarWidth, isMobile } from '$stores';
	import Button from '../Button.svelte';
	import Select from '../Select.svelte';

	export let collections: string[] = ['default'];
	export let selectedCollection = 'default';
	export let documentCount = 0;
	export let tagCount = 0;
	export let embeddingCount = 0;

	$: collectionOptions = collections.map((c) => ({ value: c, label: c }));

	function handleOverlayClick() {
		if ($isMobile) {
			sidebar.close();
		}
	}
</script>

{#if $isMobile && $isSidebarOpen}
	<div
		class="sidebar-overlay"
		on:click={handleOverlayClick}
		on:keydown={(e) => e.key === 'Escape' && sidebar.close()}
		role="presentation"
	/>
{/if}

<aside
	class="sidebar"
	class:sidebar--open={$isSidebarOpen}
	class:sidebar--mobile={$isMobile}
	style:--sidebar-current-width="{$sidebarWidth}px"
	aria-label="Document library"
>
	<div class="sidebar__content">
		<!-- Collection Selector -->
		<section class="sidebar__section">
			<Select
				bind:value={selectedCollection}
				options={collectionOptions}
				label="Collection"
			/>
		</section>

		<!-- Library Stats -->
		<section class="sidebar__section sidebar__stats">
			<div class="sidebar__stat">
				<span class="sidebar__stat-value">{documentCount}</span>
				<span class="sidebar__stat-label">documents</span>
			</div>
			<div class="sidebar__stat">
				<span class="sidebar__stat-value">{tagCount}</span>
				<span class="sidebar__stat-label">tags</span>
			</div>
			<div class="sidebar__stat">
				<span class="sidebar__stat-value">{embeddingCount}</span>
				<span class="sidebar__stat-label">embeddings</span>
			</div>
		</section>

		<!-- Document List -->
		<section class="sidebar__section sidebar__documents">
			<h3 class="sidebar__heading">Documents</h3>
			<div class="sidebar__document-list">
				<slot name="documents">
					<p class="sidebar__empty">No documents yet</p>
				</slot>
			</div>
		</section>

		<!-- Tags -->
		<section class="sidebar__section sidebar__tags">
			<h3 class="sidebar__heading">Tags</h3>
			<div class="sidebar__tag-list">
				<slot name="tags">
					<p class="sidebar__empty">No tags</p>
				</slot>
			</div>
		</section>

		<!-- Upload Zone -->
		<section class="sidebar__section sidebar__upload">
			<slot name="upload">
				<div class="sidebar__upload-zone">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
					</svg>
					<p>Drop files here or click to upload</p>
				</div>
			</slot>
		</section>
	</div>
</aside>

<style>
	.sidebar-overlay {
		position: fixed;
		inset: 0;
		background-color: rgba(0, 0, 0, 0.5);
		z-index: calc(var(--z-sticky) - 1);
	}

	.sidebar {
		position: fixed;
		top: var(--header-height);
		left: 0;
		bottom: 0;
		width: var(--sidebar-current-width);
		background-color: var(--color-bg-secondary);
		border-right: 1px solid var(--color-border-light);
		transform: translateX(0);
		transition: transform var(--transition-base);
		z-index: var(--z-sticky);
		overflow: hidden;
	}

	.sidebar:not(.sidebar--open) {
		transform: translateX(-100%);
	}

	.sidebar--mobile {
		width: 100%;
		max-width: 320px;
	}

	.sidebar__content {
		display: flex;
		flex-direction: column;
		height: 100%;
		padding: var(--space-4);
		overflow-y: auto;
	}

	.sidebar__section {
		padding: var(--space-3) 0;
	}

	.sidebar__section:not(:last-child) {
		border-bottom: 1px solid var(--color-border-light);
	}

	.sidebar__heading {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: var(--space-2);
	}

	.sidebar__stats {
		display: flex;
		gap: var(--space-4);
	}

	.sidebar__stat {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.sidebar__stat-value {
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-text-primary);
	}

	.sidebar__stat-label {
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.sidebar__documents {
		flex: 1;
		min-height: 200px;
	}

	.sidebar__document-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	.sidebar__tag-list {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-2);
	}

	.sidebar__empty {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
		text-align: center;
		padding: var(--space-4);
	}

	.sidebar__upload-zone {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--space-2);
		height: var(--upload-zone-height);
		padding: var(--space-4);
		border: 2px dashed var(--color-border-medium);
		border-radius: var(--radius-lg);
		color: var(--color-text-muted);
		text-align: center;
		cursor: pointer;
		transition: border-color var(--transition-fast), background-color var(--transition-fast);
	}

	.sidebar__upload-zone:hover {
		border-color: var(--color-primary);
		background-color: var(--color-primary-light);
	}

	.sidebar__upload-zone p {
		font-size: var(--font-size-sm);
		margin: 0;
	}
</style>
