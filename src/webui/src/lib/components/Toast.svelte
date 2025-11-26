<!--
  Toast Component
  ragged WebUI v0.7.3

  Usage: Use via toast store
  import { addToast } from '$stores/toast';
  addToast({ type: 'success', title: 'Saved!', message: 'Changes saved.' });
-->
<script lang="ts">
	import { fade, fly } from 'svelte/transition';
	import type { ToastMessage } from '$types';

	export let toast: ToastMessage;
	export let onDismiss: (id: string) => void;

	const icons: Record<ToastMessage['type'], string> = {
		success: '✓',
		error: '✕',
		warning: '⚠',
		info: 'ℹ'
	};

	function dismiss() {
		onDismiss(toast.id);
	}
</script>

<div
	class="toast toast--{toast.type}"
	role="alert"
	aria-live="polite"
	in:fly={{ x: 300, duration: 200 }}
	out:fade={{ duration: 150 }}
>
	<span class="toast__icon" aria-hidden="true">
		{icons[toast.type]}
	</span>

	<div class="toast__content">
		<p class="toast__title">{toast.title}</p>
		{#if toast.message}
			<p class="toast__message">{toast.message}</p>
		{/if}
	</div>

	<button
		class="toast__close"
		on:click={dismiss}
		aria-label="Dismiss notification"
	>
		<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
			<path d="M18 6L6 18M6 6l12 12" />
		</svg>
	</button>
</div>

<style>
	.toast {
		display: flex;
		align-items: flex-start;
		gap: var(--space-3);
		width: 100%;
		max-width: 400px;
		padding: var(--space-4);
		background-color: var(--color-bg);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-lg);
		border-left: 4px solid;
	}

	.toast--success {
		border-left-color: var(--color-success);
	}

	.toast--error {
		border-left-color: var(--color-danger);
	}

	.toast--warning {
		border-left-color: var(--color-warning);
	}

	.toast--info {
		border-left-color: var(--color-info);
	}

	.toast__icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-bold);
		border-radius: var(--radius-full);
		flex-shrink: 0;
	}

	.toast--success .toast__icon {
		background-color: var(--color-success-light);
		color: var(--color-success);
	}

	.toast--error .toast__icon {
		background-color: var(--color-danger-light);
		color: var(--color-danger);
	}

	.toast--warning .toast__icon {
		background-color: var(--color-warning-light);
		color: var(--color-warning);
	}

	.toast--info .toast__icon {
		background-color: var(--color-info-light);
		color: var(--color-info);
	}

	.toast__content {
		flex: 1;
		min-width: 0;
	}

	.toast__title {
		margin: 0;
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-primary);
	}

	.toast__message {
		margin: var(--space-1) 0 0;
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
	}

	.toast__close {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		color: var(--color-text-muted);
		background: none;
		border: none;
		border-radius: var(--radius-sm);
		cursor: pointer;
		transition: color var(--transition-fast), background-color var(--transition-fast);
		flex-shrink: 0;
	}

	.toast__close:hover {
		color: var(--color-text-primary);
		background-color: var(--color-bg-secondary);
	}
</style>
