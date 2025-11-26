<!--
  Storage Chart Component
  ragged WebUI v0.7.3

  Displays storage usage breakdown
-->
<script lang="ts">
	import type { StorageCategory } from '$types';

	export let categories: StorageCategory[] = [];
	export let totalSizeMb = 0;

	const colours = [
		'#4c6ef5', // primary
		'#40c057', // success
		'#fab005', // warning
		'#7950f2', // purple
		'#15aabf', // cyan
		'#e64980', // pink
		'#fd7e14'  // orange
	];

	function formatSize(sizeMb: number): string {
		if (sizeMb >= 1024) {
			return `${(sizeMb / 1024).toFixed(1)} GB`;
		}
		return `${sizeMb.toFixed(1)} MB`;
	}

	$: sortedCategories = [...categories].sort((a, b) => b.size_mb - a.size_mb);
</script>

<div class="storage-chart">
	<div class="storage-chart__header">
		<h3 class="storage-chart__title">Storage Usage</h3>
		<p class="storage-chart__total">{formatSize(totalSizeMb)}</p>
	</div>

	<div class="storage-chart__bar">
		{#each sortedCategories as category, index}
			{@const colour = colours[index % colours.length]}
			<div
				class="storage-chart__segment"
				style="width: {category.percentage}%; background-color: {colour}"
				title="{category.name}: {formatSize(category.size_mb)} ({category.percentage}%)"
			/>
		{/each}
	</div>

	<div class="storage-chart__legend">
		{#each sortedCategories as category, index}
			{@const colour = colours[index % colours.length]}
			<div class="storage-chart__legend-item">
				<span
					class="storage-chart__legend-colour"
					style="background-color: {colour}"
				/>
				<span class="storage-chart__legend-name">{category.name}</span>
				<span class="storage-chart__legend-size">{formatSize(category.size_mb)}</span>
				<span class="storage-chart__legend-percent">{category.percentage}%</span>
			</div>
		{/each}
	</div>
</div>

<style>
	.storage-chart {
		padding: var(--space-5);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
	}

	.storage-chart__header {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		margin-bottom: var(--space-4);
	}

	.storage-chart__title {
		margin: 0;
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
	}

	.storage-chart__total {
		margin: 0;
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-text-primary);
	}

	.storage-chart__bar {
		display: flex;
		height: 24px;
		overflow: hidden;
		background-color: var(--color-bg-tertiary);
		border-radius: var(--radius-md);
	}

	.storage-chart__segment {
		height: 100%;
		transition: width var(--transition-normal);
	}

	.storage-chart__segment:first-child {
		border-radius: var(--radius-md) 0 0 var(--radius-md);
	}

	.storage-chart__segment:last-child {
		border-radius: 0 var(--radius-md) var(--radius-md) 0;
	}

	.storage-chart__segment:only-child {
		border-radius: var(--radius-md);
	}

	.storage-chart__legend {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-3);
		margin-top: var(--space-4);
	}

	.storage-chart__legend-item {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		font-size: var(--font-size-sm);
	}

	.storage-chart__legend-colour {
		width: 12px;
		height: 12px;
		border-radius: var(--radius-sm);
	}

	.storage-chart__legend-name {
		color: var(--color-text-primary);
	}

	.storage-chart__legend-size {
		color: var(--color-text-secondary);
	}

	.storage-chart__legend-percent {
		color: var(--color-text-muted);
		font-variant-numeric: tabular-nums;
	}
</style>
