<!--
  Progress Component
  ragged WebUI v0.7.3

  Usage:
  <Progress value={75} max={100} />
  <Progress indeterminate />
-->
<script lang="ts">
	export let value: number = 0;
	export let max: number = 100;
	export let indeterminate = false;
	export let size: 'sm' | 'md' | 'lg' = 'md';
	export let variant: 'default' | 'success' | 'warning' | 'danger' = 'default';
	export let showValue = false;
	export let label: string | undefined = undefined;

	$: percentage = Math.min(Math.max((value / max) * 100, 0), 100);
	$: displayValue = `${Math.round(percentage)}%`;
</script>

<div
	class="progress progress--{size}"
	role="progressbar"
	aria-valuenow={indeterminate ? undefined : value}
	aria-valuemin={0}
	aria-valuemax={max}
	aria-label={label}
>
	{#if label || showValue}
		<div class="progress__header">
			{#if label}
				<span class="progress__label">{label}</span>
			{/if}
			{#if showValue && !indeterminate}
				<span class="progress__value">{displayValue}</span>
			{/if}
		</div>
	{/if}

	<div class="progress__track">
		<div
			class="progress__bar progress__bar--{variant}"
			class:progress__bar--indeterminate={indeterminate}
			style:width={indeterminate ? '100%' : `${percentage}%`}
		/>
	</div>
</div>

<style>
	.progress {
		width: 100%;
	}

	.progress__header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--space-1);
	}

	.progress__label {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-primary);
	}

	.progress__value {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-secondary);
		font-variant-numeric: tabular-nums;
	}

	.progress__track {
		width: 100%;
		background-color: var(--color-bg-tertiary);
		border-radius: var(--radius-full);
		overflow: hidden;
	}

	.progress--sm .progress__track {
		height: 4px;
	}

	.progress--md .progress__track {
		height: 8px;
	}

	.progress--lg .progress__track {
		height: 12px;
	}

	.progress__bar {
		height: 100%;
		border-radius: var(--radius-full);
		transition: width var(--transition-slow);
	}

	.progress__bar--default {
		background-color: var(--color-primary);
	}

	.progress__bar--success {
		background-color: var(--color-success);
	}

	.progress__bar--warning {
		background-color: var(--color-warning);
	}

	.progress__bar--danger {
		background-color: var(--color-danger);
	}

	.progress__bar--indeterminate {
		animation: indeterminate 1.5s ease-in-out infinite;
		transform-origin: left;
	}

	@keyframes indeterminate {
		0% {
			transform: translateX(-100%) scaleX(0.3);
		}
		50% {
			transform: translateX(0%) scaleX(0.5);
		}
		100% {
			transform: translateX(100%) scaleX(0.3);
		}
	}
</style>
