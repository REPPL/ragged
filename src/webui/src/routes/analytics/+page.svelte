<!--
  Analytics Page
  ragged WebUI v0.7.3

  System analytics and metrics dashboard
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import type { PerformanceMetrics, StorageMetrics } from '$types';
	import { addToast } from '$stores';
	import { api } from '$api';
	import { MetricCard, StorageChart, PerformanceChart } from '$lib/components/analytics';
	import Select from '$lib/components/Select.svelte';
	import Button from '$lib/components/Button.svelte';
	import Skeleton from '$lib/components/Skeleton.svelte';

	let performance: PerformanceMetrics | null = null;
	let storage: StorageMetrics | null = null;
	let loading = true;
	let error: string | null = null;

	let period = '24h';

	const periodOptions = [
		{ value: '1h', label: 'Last hour' },
		{ value: '24h', label: 'Last 24 hours' },
		{ value: '7d', label: 'Last 7 days' },
		{ value: '30d', label: 'Last 30 days' }
	];

	async function loadAnalytics() {
		loading = true;
		error = null;
		try {
			const [perfData, storageData] = await Promise.all([
				api.analytics.performance(period),
				api.analytics.storage()
			]);
			performance = perfData;
			storage = storageData;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load analytics';
			addToast({
				type: 'error',
				title: 'Failed to load analytics',
				message: error
			});
		} finally {
			loading = false;
		}
	}

	function handlePeriodChange(event: Event) {
		const target = event.target as HTMLSelectElement;
		period = target.value;
		loadAnalytics();
	}

	onMount(() => {
		loadAnalytics();
	});
</script>

<svelte:head>
	<title>Analytics - ragged</title>
</svelte:head>

<div class="analytics-page">
	<div class="analytics-page__header">
		<div class="analytics-page__title-section">
			<h1 class="analytics-page__title">Analytics</h1>
			<p class="analytics-page__subtitle">
				Monitor system performance and usage
			</p>
		</div>

		<div class="analytics-page__controls">
			<Select
				value={period}
				options={periodOptions}
				label="Time period"
				hideLabel
				on:change={handlePeriodChange}
			/>
			<Button variant="ghost" size="sm" on:click={loadAnalytics}>
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="23 4 23 10 17 10" />
					<polyline points="1 20 1 14 7 14" />
					<path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
				</svg>
				Refresh
			</Button>
		</div>
	</div>

	{#if error}
		<div class="analytics-page__error" role="alert">
			<p>{error}</p>
			<Button variant="primary" size="sm" on:click={loadAnalytics}>
				Try again
			</Button>
		</div>
	{:else if loading}
		<div class="analytics-page__loading">
			<div class="analytics-page__metrics-grid">
				{#each Array(4) as _}
					<Skeleton height="100px" />
				{/each}
			</div>
			<Skeleton height="250px" />
			<Skeleton height="250px" />
		</div>
	{:else}
		<!-- Key Metrics -->
		<div class="analytics-page__metrics-grid">
			<MetricCard
				label="Total Queries"
				value={performance?.query_count ?? 0}
				icon="🔍"
			/>
			<MetricCard
				label="Average Latency"
				value={performance ? (performance.avg_latency_ms / 1000).toFixed(2) : '0'}
				unit="s"
				icon="⚡"
			/>
			<MetricCard
				label="Cache Hit Rate"
				value={performance ? (performance.cache_hit_rate * 100).toFixed(0) : '0'}
				unit="%"
				icon="💾"
			/>
			<MetricCard
				label="Total Storage"
				value={storage ? (storage.total_size_gb).toFixed(1) : '0'}
				unit=" GB"
				icon="📦"
			/>
		</div>

		<!-- Charts -->
		<div class="analytics-page__charts">
			<PerformanceChart metrics={performance} />

			{#if storage}
				<StorageChart
					categories={storage.categories}
					totalSizeMb={storage.total_size_mb}
				/>
			{/if}
		</div>

		<!-- Recommendations -->
		{#if storage?.recommendations && storage.recommendations.length > 0}
			<div class="analytics-page__recommendations">
				<h2 class="analytics-page__section-title">Recommendations</h2>
				<ul class="analytics-page__recommendations-list">
					{#each storage.recommendations as recommendation}
						<li class="analytics-page__recommendation">
							<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<circle cx="12" cy="12" r="10" />
								<line x1="12" y1="16" x2="12" y2="12" />
								<line x1="12" y1="8" x2="12.01" y2="8" />
							</svg>
							{recommendation}
						</li>
					{/each}
				</ul>
			</div>
		{/if}

		<!-- Growth Projection -->
		{#if storage?.growth_projection}
			<div class="analytics-page__projection">
				<h2 class="analytics-page__section-title">Storage Growth Projection</h2>
				<div class="analytics-page__projection-grid">
					<div class="analytics-page__projection-item">
						<span class="analytics-page__projection-label">Daily growth</span>
						<span class="analytics-page__projection-value">
							{(storage.growth_projection.daily_growth_bytes / 1024 / 1024).toFixed(2)} MB
						</span>
					</div>
					<div class="analytics-page__projection-item">
						<span class="analytics-page__projection-label">Weekly growth</span>
						<span class="analytics-page__projection-value">
							{(storage.growth_projection.weekly_growth_bytes / 1024 / 1024).toFixed(2)} MB
						</span>
					</div>
					<div class="analytics-page__projection-item">
						<span class="analytics-page__projection-label">Monthly growth</span>
						<span class="analytics-page__projection-value">
							{(storage.growth_projection.monthly_growth_bytes / 1024 / 1024).toFixed(2)} MB
						</span>
					</div>
					{#if storage.growth_projection.days_until_full !== null}
						<div class="analytics-page__projection-item">
							<span class="analytics-page__projection-label">Days until full</span>
							<span class="analytics-page__projection-value">
								{storage.growth_projection.days_until_full}
							</span>
						</div>
					{/if}
				</div>
			</div>
		{/if}
	{/if}
</div>

<style>
	.analytics-page {
		display: flex;
		flex-direction: column;
		gap: var(--space-6);
		max-width: 1200px;
		margin: 0 auto;
	}

	.analytics-page__header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: var(--space-4);
		flex-wrap: wrap;
	}

	.analytics-page__title-section {
		flex: 1;
	}

	.analytics-page__title {
		margin: 0;
		font-size: var(--font-size-3xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-text-primary);
	}

	.analytics-page__subtitle {
		margin: var(--space-2) 0 0;
		font-size: var(--font-size-lg);
		color: var(--color-text-muted);
	}

	.analytics-page__controls {
		display: flex;
		align-items: center;
		gap: var(--space-3);
	}

	.analytics-page__error {
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

	.analytics-page__loading {
		display: flex;
		flex-direction: column;
		gap: var(--space-6);
	}

	.analytics-page__metrics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: var(--space-4);
	}

	.analytics-page__charts {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
		gap: var(--space-6);
	}

	.analytics-page__section-title {
		margin: 0 0 var(--space-4);
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
	}

	.analytics-page__recommendations {
		padding: var(--space-5);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
	}

	.analytics-page__recommendations-list {
		margin: 0;
		padding: 0;
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.analytics-page__recommendation {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
	}

	.analytics-page__recommendation svg {
		color: var(--color-warning);
		flex-shrink: 0;
	}

	.analytics-page__projection {
		padding: var(--space-5);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
	}

	.analytics-page__projection-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: var(--space-4);
	}

	.analytics-page__projection-item {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.analytics-page__projection-label {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.analytics-page__projection-value {
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
	}

	@media (max-width: 640px) {
		.analytics-page__header {
			flex-direction: column;
			align-items: stretch;
		}

		.analytics-page__controls {
			justify-content: space-between;
		}

		.analytics-page__charts {
			grid-template-columns: 1fr;
		}
	}
</style>
