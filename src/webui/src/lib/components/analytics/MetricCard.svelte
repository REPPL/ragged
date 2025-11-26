<!--
  Metric Card Component
  ragged WebUI v0.7.3

  Displays a single metric with label and optional trend
-->
<script lang="ts">
	export let label: string;
	export let value: string | number;
	export let unit = '';
	export let trend: 'up' | 'down' | 'neutral' | null = null;
	export let trendValue = '';
	export let icon = '';
</script>

<div class="metric-card">
	{#if icon}
		<span class="metric-card__icon" aria-hidden="true">{icon}</span>
	{/if}

	<div class="metric-card__content">
		<p class="metric-card__label">{label}</p>
		<p class="metric-card__value">
			{value}{unit}
		</p>

		{#if trend && trendValue}
			<p
				class="metric-card__trend"
				class:metric-card__trend--up={trend === 'up'}
				class:metric-card__trend--down={trend === 'down'}
			>
				{#if trend === 'up'}
					<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<polyline points="18 15 12 9 6 15" />
					</svg>
				{:else if trend === 'down'}
					<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<polyline points="6 9 12 15 18 9" />
					</svg>
				{/if}
				{trendValue}
			</p>
		{/if}
	</div>
</div>

<style>
	.metric-card {
		display: flex;
		align-items: flex-start;
		gap: var(--space-4);
		padding: var(--space-5);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
	}

	.metric-card__icon {
		font-size: var(--font-size-2xl);
	}

	.metric-card__content {
		flex: 1;
	}

	.metric-card__label {
		margin: 0;
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.metric-card__value {
		margin: var(--space-1) 0 0;
		font-size: var(--font-size-2xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-text-primary);
		font-variant-numeric: tabular-nums;
	}

	.metric-card__trend {
		display: flex;
		align-items: center;
		gap: var(--space-1);
		margin: var(--space-2) 0 0;
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.metric-card__trend--up {
		color: var(--color-success);
	}

	.metric-card__trend--down {
		color: var(--color-danger);
	}
</style>
