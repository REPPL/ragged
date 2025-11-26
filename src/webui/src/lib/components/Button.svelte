<!--
  Button Component
  ragged WebUI v0.7.3

  Usage:
  <Button variant="primary" size="md" on:click={handleClick}>
    Click me
  </Button>
-->
<script lang="ts">
	import type { HTMLButtonAttributes } from 'svelte/elements';
	import type { ButtonVariant, ButtonSize } from '$types';

	interface $$Props extends HTMLButtonAttributes {
		variant?: ButtonVariant;
		size?: ButtonSize;
		loading?: boolean;
		disabled?: boolean;
		fullWidth?: boolean;
		iconOnly?: boolean;
	}

	export let variant: ButtonVariant = 'primary';
	export let size: ButtonSize = 'md';
	export let loading = false;
	export let disabled = false;
	export let fullWidth = false;
	export let iconOnly = false;

	$: isDisabled = disabled || loading;
</script>

<button
	class="btn btn--{variant} btn--{size}"
	class:btn--loading={loading}
	class:btn--full-width={fullWidth}
	class:btn--icon-only={iconOnly}
	disabled={isDisabled}
	aria-busy={loading}
	{...$$restProps}
	on:click
	on:focus
	on:blur
	on:mouseenter
	on:mouseleave
>
	{#if loading}
		<span class="btn__spinner" aria-hidden="true">
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-linecap="round" />
			</svg>
		</span>
	{/if}

	<span class="btn__content" class:btn__content--hidden={loading && iconOnly}>
		<slot />
	</span>
</button>

<style>
	.btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-2);
		font-family: var(--font-sans);
		font-weight: var(--font-weight-medium);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition:
			background-color var(--transition-fast),
			border-color var(--transition-fast),
			color var(--transition-fast),
			box-shadow var(--transition-fast);
		white-space: nowrap;
		user-select: none;
		position: relative;
	}

	.btn:focus-visible {
		outline: none;
		box-shadow: var(--shadow-focus);
	}

	.btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	/* Sizes */
	.btn--sm {
		height: 32px;
		padding: 0 var(--space-3);
		font-size: var(--font-size-sm);
	}

	.btn--md {
		height: 40px;
		padding: 0 var(--space-4);
		font-size: var(--font-size-base);
	}

	.btn--lg {
		height: 48px;
		padding: 0 var(--space-6);
		font-size: var(--font-size-lg);
	}

	/* Icon only */
	.btn--icon-only.btn--sm {
		width: 32px;
		padding: 0;
	}

	.btn--icon-only.btn--md {
		width: 40px;
		padding: 0;
	}

	.btn--icon-only.btn--lg {
		width: 48px;
		padding: 0;
	}

	/* Variants */
	.btn--primary {
		background-color: var(--color-primary);
		color: var(--color-text-inverse);
		border: none;
	}

	.btn--primary:hover:not(:disabled) {
		background-color: var(--color-primary-hover);
	}

	.btn--primary:active:not(:disabled) {
		background-color: var(--color-primary-active);
	}

	.btn--secondary {
		background-color: var(--color-bg);
		color: var(--color-text-primary);
		border: 1px solid var(--color-border-medium);
	}

	.btn--secondary:hover:not(:disabled) {
		background-color: var(--color-bg-secondary);
		border-color: var(--color-border-dark);
	}

	.btn--ghost {
		background-color: transparent;
		color: var(--color-text-secondary);
		border: none;
	}

	.btn--ghost:hover:not(:disabled) {
		background-color: var(--color-bg-secondary);
		color: var(--color-text-primary);
	}

	.btn--danger {
		background-color: var(--color-danger);
		color: var(--color-text-inverse);
		border: none;
	}

	.btn--danger:hover:not(:disabled) {
		background-color: #b02525;
	}

	.btn--success {
		background-color: var(--color-success);
		color: var(--color-text-inverse);
		border: none;
	}

	.btn--success:hover:not(:disabled) {
		background-color: #237032;
	}

	/* Full width */
	.btn--full-width {
		width: 100%;
	}

	/* Loading */
	.btn--loading {
		pointer-events: none;
	}

	.btn__spinner {
		width: 1em;
		height: 1em;
		animation: spin 1s linear infinite;
	}

	.btn__spinner svg {
		width: 100%;
		height: 100%;
	}

	.btn__content {
		display: inline-flex;
		align-items: center;
		gap: var(--space-2);
	}

	.btn__content--hidden {
		visibility: hidden;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
