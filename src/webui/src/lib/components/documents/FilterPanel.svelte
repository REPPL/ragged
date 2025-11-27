<!--
  Filter Panel Component
  ragged WebUI v0.9.2

  Advanced faceted search panel for document filtering
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { DocumentType, DocumentFilters, Collection } from '$types';
	import DateRangePicker from '../common/DateRangePicker.svelte';
	import Button from '../Button.svelte';

	export let filters: DocumentFilters = {
		collection: null,
		tags: [],
		types: [],
		dateRange: null,
		search: ''
	};

	export let collections: Collection[] = [];
	export let availableTags: string[] = [];
	export let collapsed = false;

	const dispatch = createEventDispatcher<{
		change: DocumentFilters;
		clear: void;
	}>();

	const documentTypes: { value: DocumentType; label: string; icon: string }[] = [
		{ value: 'pdf', label: 'PDF', icon: '📄' },
		{ value: 'markdown', label: 'Markdown', icon: '📝' },
		{ value: 'text', label: 'Text', icon: '📃' },
		{ value: 'html', label: 'HTML', icon: '🌐' },
		{ value: 'code', label: 'Code', icon: '💻' }
	];

	$: activeFilterCount = [
		filters.collection ? 1 : 0,
		filters.tags.length,
		filters.types.length,
		filters.dateRange ? 1 : 0
	].reduce((a, b) => a + b, 0);

	function toggleType(type: DocumentType) {
		const newTypes = filters.types.includes(type)
			? filters.types.filter((t) => t !== type)
			: [...filters.types, type];

		updateFilters({ types: newTypes });
	}

	function toggleTag(tag: string) {
		const newTags = filters.tags.includes(tag)
			? filters.tags.filter((t) => t !== tag)
			: [...filters.tags, tag];

		updateFilters({ tags: newTags });
	}

	function setCollection(collectionId: string | null) {
		updateFilters({ collection: collectionId });
	}

	function handleDateChange(event: CustomEvent<{ start: Date | null; end: Date | null }>) {
		const { start, end } = event.detail;
		updateFilters({
			dateRange: start && end ? { start, end } : null
		});
	}

	function updateFilters(partial: Partial<DocumentFilters>) {
		filters = { ...filters, ...partial };
		dispatch('change', filters);
	}

	function clearAllFilters() {
		filters = {
			collection: null,
			tags: [],
			types: [],
			dateRange: null,
			search: ''
		};
		dispatch('clear');
		dispatch('change', filters);
	}

	function toggleCollapsed() {
		collapsed = !collapsed;
	}
</script>

<aside class="filter-panel" class:filter-panel--collapsed={collapsed}>
	<div class="filter-panel__header">
		<button
			type="button"
			class="filter-panel__toggle"
			on:click={toggleCollapsed}
			aria-expanded={!collapsed}
			aria-controls="filter-content"
		>
			<svg
				width="20"
				height="20"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				class="filter-panel__icon"
				class:filter-panel__icon--rotated={collapsed}
			>
				<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
			</svg>
			<span class="filter-panel__title">Filters</span>
			{#if activeFilterCount > 0}
				<span class="filter-panel__badge">{activeFilterCount}</span>
			{/if}
		</button>

		{#if activeFilterCount > 0 && !collapsed}
			<Button variant="ghost" size="sm" on:click={clearAllFilters}>
				Clear all
			</Button>
		{/if}
	</div>

	{#if !collapsed}
		<div id="filter-content" class="filter-panel__content">
			<!-- Date Range -->
			<section class="filter-panel__section">
				<h3 class="filter-panel__section-title">Date</h3>
				<DateRangePicker
					startDate={filters.dateRange?.start ?? null}
					endDate={filters.dateRange?.end ?? null}
					on:change={handleDateChange}
				/>
			</section>

			<!-- Collections -->
			{#if collections.length > 0}
				<section class="filter-panel__section">
					<h3 class="filter-panel__section-title">Collection</h3>
					<div class="filter-panel__options">
						<button
							type="button"
							class="filter-panel__option"
							class:filter-panel__option--active={filters.collection === null}
							on:click={() => setCollection(null)}
						>
							<span class="filter-panel__option-icon">📚</span>
							<span class="filter-panel__option-label">All collections</span>
						</button>
						{#each collections as collection}
							<button
								type="button"
								class="filter-panel__option"
								class:filter-panel__option--active={filters.collection === collection.id}
								on:click={() => setCollection(collection.id)}
							>
								<span class="filter-panel__option-icon">{collection.icon || '📁'}</span>
								<span class="filter-panel__option-label">{collection.name}</span>
								<span class="filter-panel__option-count">{collection.document_count}</span>
							</button>
						{/each}
					</div>
				</section>
			{/if}

			<!-- Document Types -->
			<section class="filter-panel__section">
				<h3 class="filter-panel__section-title">Type</h3>
				<div class="filter-panel__chips">
					{#each documentTypes as type}
						<button
							type="button"
							class="filter-panel__chip"
							class:filter-panel__chip--active={filters.types.includes(type.value)}
							on:click={() => toggleType(type.value)}
							aria-pressed={filters.types.includes(type.value)}
						>
							<span>{type.icon}</span>
							<span>{type.label}</span>
						</button>
					{/each}
				</div>
			</section>

			<!-- Tags -->
			{#if availableTags.length > 0}
				<section class="filter-panel__section">
					<h3 class="filter-panel__section-title">Tags</h3>
					<div class="filter-panel__chips">
						{#each availableTags as tag}
							<button
								type="button"
								class="filter-panel__chip"
								class:filter-panel__chip--active={filters.tags.includes(tag)}
								on:click={() => toggleTag(tag)}
								aria-pressed={filters.tags.includes(tag)}
							>
								<span>#</span>
								<span>{tag}</span>
							</button>
						{/each}
					</div>
				</section>
			{/if}
		</div>
	{/if}
</aside>

<style>
	.filter-panel {
		display: flex;
		flex-direction: column;
		width: 280px;
		min-width: 280px;
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
		overflow: hidden;
		transition: width var(--transition-normal);
	}

	.filter-panel--collapsed {
		width: auto;
		min-width: auto;
	}

	.filter-panel__header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--space-3) var(--space-4);
		border-bottom: 1px solid var(--color-border-light);
		background-color: var(--color-bg-secondary);
	}

	.filter-panel__toggle {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: 0;
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
		background: none;
		border: none;
		cursor: pointer;
	}

	.filter-panel__icon {
		transition: transform var(--transition-fast);
	}

	.filter-panel__icon--rotated {
		transform: rotate(-90deg);
	}

	.filter-panel__title {
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.filter-panel__badge {
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 20px;
		height: 20px;
		padding: 0 var(--space-1);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-bold);
		color: white;
		background-color: var(--color-primary);
		border-radius: var(--radius-full);
	}

	.filter-panel__content {
		padding: var(--space-4);
		overflow-y: auto;
	}

	.filter-panel__section {
		margin-bottom: var(--space-5);
	}

	.filter-panel__section:last-child {
		margin-bottom: 0;
	}

	.filter-panel__section-title {
		margin: 0 0 var(--space-3);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.filter-panel__options {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.filter-panel__option {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		width: 100%;
		padding: var(--space-2) var(--space-3);
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		text-align: left;
		background: none;
		border: none;
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.filter-panel__option:hover {
		background-color: var(--color-bg-secondary);
		color: var(--color-text-primary);
	}

	.filter-panel__option--active {
		background-color: var(--color-primary-light);
		color: var(--color-primary);
	}

	.filter-panel__option-icon {
		flex-shrink: 0;
	}

	.filter-panel__option-label {
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.filter-panel__option-count {
		flex-shrink: 0;
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.filter-panel__chips {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-2);
	}

	.filter-panel__chip {
		display: flex;
		align-items: center;
		gap: var(--space-1);
		padding: var(--space-1) var(--space-2);
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		background-color: var(--color-bg-tertiary);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-full);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.filter-panel__chip:hover {
		border-color: var(--color-primary);
		background-color: var(--color-bg);
	}

	.filter-panel__chip--active {
		background-color: var(--color-primary);
		border-color: var(--color-primary);
		color: white;
	}

	@media (max-width: 1024px) {
		.filter-panel {
			width: 100%;
			min-width: 100%;
		}
	}
</style>
