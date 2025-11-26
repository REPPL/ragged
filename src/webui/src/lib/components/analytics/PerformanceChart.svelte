<!--
  Performance Chart Component
  ragged WebUI v0.7.3

  Displays query performance metrics with bars
-->
<script lang="ts">
	import type { PerformanceMetrics } from '$types';

	export let metrics: PerformanceMetrics | null = null;

	function formatLatency(ms: number): string {
		if (ms >= 1000) {
			return `${(ms / 1000).toFixed(2)}s`;
		}
		return `${ms.toFixed(0)}ms`;
	}

	$: latencyData = metrics
		? [
				{ label: 'p50', value: metrics.latency_p50, max: metrics.latency_p99 },
				{ label: 'p95', value: metrics.latency_p95, max: metrics.latency_p99 },
				{ label: 'p99', value: metrics.latency_p99, max: metrics.latency_p99 }
			]
		: [];
</script>

<div class="performance-chart">
	<div class="performance-chart__header">
		<h3 class="performance-chart__title">Query Latency</h3>
		{#if metrics}
			<p class="performance-chart__subtitle">
				Average: {formatLatency(metrics.avg_latency_ms)}
			</p>
		{/if}
	</div>

	{#if metrics}
		<div class="performance-chart__bars">
			{#each latencyData as item}
				{@const percentage = (item.value / item.max) * 100}
				<div class="performance-chart__bar-row">
					<span class="performance-chart__bar-label">{item.label}</span>
					<div class="performance-chart__bar-track">
						<div
							class="performance-chart__bar-fill"
							style="width: {percentage}%"
						/>
					</div>
					<span class="performance-chart__bar-value">
						{formatLatency(item.value)}
					</span>
				</div>
			{/each}
		</div>

		<div class="performance-chart__stats">
			<div class="performance-chart__stat">
				<span class="performance-chart__stat-label">Queries</span>
				<span class="performance-chart__stat-value">{metrics.query_count}</span>
			</div>
			<div class="performance-chart__stat">
				<span class="performance-chart__stat-label">Cache hit rate</span>
				<span class="performance-chart__stat-value">
					{(metrics.cache_hit_rate * 100).toFixed(0)}%
				</span>
			</div>
			<div class="performance-chart__stat">
				<span class="performance-chart__stat-label">Errors</span>
				<span
					class="performance-chart__stat-value"
					class:performance-chart__stat-value--error={metrics.error_count > 0}
				>
					{metrics.error_count}
				</span>
			</div>
		</div>
	{:else}
		<p class="performance-chart__empty">No performance data available</p>
	{/if}
</div>

<style>
	.performance-chart {
		padding: var(--space-5);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
	}

	.performance-chart__header {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		margin-bottom: var(--space-4);
	}

	.performance-chart__title {
		margin: 0;
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
	}

	.performance-chart__subtitle {
		margin: 0;
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.performance-chart__bars {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.performance-chart__bar-row {
		display: flex;
		align-items: center;
		gap: var(--space-3);
	}

	.performance-chart__bar-label {
		width: 40px;
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-secondary);
	}

	.performance-chart__bar-track {
		flex: 1;
		height: 16px;
		background-color: var(--color-bg-tertiary);
		border-radius: var(--radius-md);
		overflow: hidden;
	}

	.performance-chart__bar-fill {
		height: 100%;
		background-color: var(--color-primary);
		border-radius: var(--radius-md);
		transition: width var(--transition-normal);
	}

	.performance-chart__bar-value {
		width: 60px;
		font-size: var(--font-size-sm);
		font-variant-numeric: tabular-nums;
		color: var(--color-text-muted);
		text-align: right;
	}

	.performance-chart__stats {
		display: flex;
		gap: var(--space-6);
		margin-top: var(--space-5);
		padding-top: var(--space-4);
		border-top: 1px solid var(--color-border-light);
	}

	.performance-chart__stat {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.performance-chart__stat-label {
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.performance-chart__stat-value {
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
	}

	.performance-chart__stat-value--error {
		color: var(--color-danger);
	}

	.performance-chart__empty {
		padding: var(--space-8);
		text-align: center;
		color: var(--color-text-muted);
	}
</style>
