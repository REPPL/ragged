<!--
  Query Options Component
  ragged WebUI v0.7.3

  Query mode tabs and options
-->
<script lang="ts">
	import Tabs from '../Tabs.svelte';
	import Select from '../Select.svelte';

	export let mode: 'text' | 'image' | 'hybrid' = 'text';
	export let topK = 5;
	export let retrievalMethod: 'vector' | 'bm25' | 'hybrid' = 'hybrid';
	export let showAdvanced = false;

	const modeTabs = [
		{ id: 'text', label: 'Text', icon: '📝' },
		{ id: 'image', label: 'Image', icon: '🖼️', disabled: true },
		{ id: 'hybrid', label: 'Hybrid', icon: '🔀', disabled: true }
	];

	const retrievalOptions = [
		{ value: 'hybrid', label: 'Hybrid (recommended)' },
		{ value: 'vector', label: 'Vector only' },
		{ value: 'bm25', label: 'BM25 only' }
	];

	const topKOptions = [
		{ value: '3', label: '3 results' },
		{ value: '5', label: '5 results' },
		{ value: '10', label: '10 results' },
		{ value: '20', label: '20 results' }
	];

	$: topKValue = String(topK);

	function handleTopKChange(event: Event) {
		const target = event.target as HTMLSelectElement;
		topK = parseInt(target.value, 10);
	}
</script>

<div class="query-options">
	<div class="query-options__row">
		<Tabs tabs={modeTabs} bind:active={mode} variant="pill" />

		<button
			type="button"
			class="query-options__toggle"
			on:click={() => (showAdvanced = !showAdvanced)}
			aria-expanded={showAdvanced}
		>
			<svg
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				class:rotated={showAdvanced}
			>
				<polyline points="6 9 12 15 18 9" />
			</svg>
			Options
		</button>
	</div>

	{#if showAdvanced}
		<div class="query-options__advanced">
			<div class="query-options__field">
				<Select
					bind:value={retrievalMethod}
					options={retrievalOptions}
					label="Retrieval method"
				/>
			</div>

			<div class="query-options__field">
				<Select
					value={topKValue}
					options={topKOptions}
					label="Results count"
					on:change={handleTopKChange}
				/>
			</div>
		</div>
	{/if}
</div>

<style>
	.query-options {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.query-options__row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-4);
	}

	.query-options__toggle {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-2) var(--space-3);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-secondary);
		background: none;
		border: none;
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: color var(--transition-fast), background-color var(--transition-fast);
	}

	.query-options__toggle:hover {
		color: var(--color-text-primary);
		background-color: var(--color-bg-secondary);
	}

	.query-options__toggle svg {
		transition: transform var(--transition-fast);
	}

	.query-options__toggle svg.rotated {
		transform: rotate(180deg);
	}

	.query-options__advanced {
		display: flex;
		gap: var(--space-4);
		padding: var(--space-4);
		background-color: var(--color-bg-secondary);
		border-radius: var(--radius-lg);
	}

	.query-options__field {
		flex: 1;
		min-width: 150px;
		max-width: 250px;
	}

	@media (max-width: 640px) {
		.query-options__row {
			flex-direction: column;
			align-items: stretch;
		}

		.query-options__advanced {
			flex-direction: column;
		}

		.query-options__field {
			max-width: none;
		}
	}
</style>
