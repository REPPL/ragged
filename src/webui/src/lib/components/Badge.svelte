<!--
  Badge Component
  ragged WebUI v0.7.3

  Usage:
  <Badge variant="success">Active</Badge>
  <Badge score={92} />
-->
<script lang="ts">
	import type { BadgeVariant } from '$types';

	export let variant: BadgeVariant = 'default';
	export let size: 'sm' | 'md' | 'lg' = 'md';
	export let score: number | undefined = undefined;
	export let removable = false;

	// Score-based variant calculation
	$: computedVariant = score !== undefined
		? score >= 90 ? 'success'
		: score >= 80 ? 'warning'
		: 'danger'
		: variant;

	$: displayValue = score !== undefined ? `${Math.round(score)}%` : undefined;
</script>

<span
	class="badge badge--{computedVariant} badge--{size}"
	class:badge--score={score !== undefined}
	{...$$restProps}
>
	{#if displayValue}
		{displayValue}
	{:else}
		<slot />
	{/if}

	{#if removable}
		<button
			type="button"
			class="badge__remove"
			on:click
			aria-label="Remove"
		>
			<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<path d="M18 6L6 18M6 6l12 12" />
			</svg>
		</button>
	{/if}
</span>

<style>
	.badge {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-1);
		font-family: var(--font-sans);
		font-weight: var(--font-weight-medium);
		border-radius: var(--radius-full);
		white-space: nowrap;
	}

	/* Sizes */
	.badge--sm {
		height: 20px;
		padding: 0 var(--space-2);
		font-size: var(--font-size-xs);
	}

	.badge--md {
		height: 24px;
		padding: 0 var(--space-3);
		font-size: var(--font-size-sm);
	}

	.badge--lg {
		height: 28px;
		padding: 0 var(--space-4);
		font-size: var(--font-size-base);
	}

	/* Variants */
	.badge--default {
		background-color: var(--color-bg-tertiary);
		color: var(--color-text-secondary);
	}

	.badge--primary {
		background-color: var(--color-primary-light);
		color: var(--color-primary);
	}

	.badge--success {
		background-color: var(--color-success-light);
		color: var(--color-success);
	}

	.badge--warning {
		background-color: var(--color-warning-light);
		color: var(--color-warning);
	}

	.badge--danger {
		background-color: var(--color-danger-light);
		color: var(--color-danger);
	}

	/* Score badge (circular) */
	.badge--score {
		width: var(--badge-score-size);
		height: var(--badge-score-size);
		padding: 0;
		border-radius: var(--radius-full);
		font-weight: var(--font-weight-bold);
	}

	.badge--score.badge--sm {
		width: 32px;
		height: 32px;
		font-size: var(--font-size-xs);
	}

	.badge--score.badge--md {
		width: var(--badge-score-size);
		height: var(--badge-score-size);
		font-size: var(--font-size-sm);
	}

	.badge--score.badge--lg {
		width: 48px;
		height: 48px;
		font-size: var(--font-size-base);
	}

	/* Remove button */
	.badge__remove {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 16px;
		height: 16px;
		margin-left: var(--space-1);
		padding: 0;
		background: none;
		border: none;
		border-radius: var(--radius-full);
		color: currentColor;
		opacity: 0.6;
		cursor: pointer;
		transition: opacity var(--transition-fast), background-color var(--transition-fast);
	}

	.badge__remove:hover {
		opacity: 1;
		background-color: rgba(0, 0, 0, 0.1);
	}
</style>
