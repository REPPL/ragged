<!--
  Toast Container Component
  ragged WebUI v0.7.3

  Renders all active toasts
-->
<script lang="ts">
	import { toasts, dismissToast } from '$stores';
	import Toast from '../Toast.svelte';
</script>

{#if $toasts.length > 0}
	<div class="toast-container" aria-live="polite" aria-label="Notifications">
		{#each $toasts as toast (toast.id)}
			<Toast {toast} onDismiss={dismissToast} />
		{/each}
	</div>
{/if}

<style>
	.toast-container {
		position: fixed;
		bottom: var(--space-4);
		right: var(--space-4);
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
		z-index: var(--z-toast);
		max-width: 100%;
		pointer-events: none;
	}

	.toast-container > :global(*) {
		pointer-events: auto;
	}

	@media (max-width: 480px) {
		.toast-container {
			left: var(--space-4);
			right: var(--space-4);
		}
	}
</style>
