<!--
  Modal Component
  ragged WebUI v0.7.3

  Usage:
  <Modal bind:open={showModal} title="Confirm" on:close={handleClose}>
    <p>Are you sure?</p>
    <svelte:fragment slot="footer">
      <Button variant="secondary" on:click={() => showModal = false}>Cancel</Button>
      <Button variant="primary" on:click={confirm}>Confirm</Button>
    </svelte:fragment>
  </Modal>
-->
<script lang="ts">
	import { createEventDispatcher, onMount, onDestroy } from 'svelte';
	import { fade, scale } from 'svelte/transition';
	import Button from './Button.svelte';

	export let open = false;
	export let title = '';
	export let size: 'sm' | 'md' | 'lg' | 'xl' = 'md';
	export let closeable = true;
	export let closeOnOverlayClick = true;
	export let closeOnEscape = true;

	const dispatch = createEventDispatcher<{ close: void }>();

	let modalElement: HTMLDivElement;
	let previousActiveElement: Element | null = null;

	function close() {
		if (closeable) {
			open = false;
			dispatch('close');
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && closeOnEscape && closeable) {
			event.preventDefault();
			close();
		}

		// Trap focus within modal
		if (event.key === 'Tab' && modalElement) {
			const focusableElements = modalElement.querySelectorAll<HTMLElement>(
				'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
			);
			const firstElement = focusableElements[0];
			const lastElement = focusableElements[focusableElements.length - 1];

			if (event.shiftKey && document.activeElement === firstElement) {
				event.preventDefault();
				lastElement?.focus();
			} else if (!event.shiftKey && document.activeElement === lastElement) {
				event.preventDefault();
				firstElement?.focus();
			}
		}
	}

	function handleOverlayClick() {
		if (closeOnOverlayClick) {
			close();
		}
	}

	$: if (open) {
		previousActiveElement = document.activeElement;
		document.body.style.overflow = 'hidden';
	} else {
		document.body.style.overflow = '';
		if (previousActiveElement instanceof HTMLElement) {
			previousActiveElement.focus();
		}
	}

	onDestroy(() => {
		document.body.style.overflow = '';
	});
</script>

<svelte:window on:keydown={open ? handleKeydown : undefined} />

{#if open}
	<div
		class="modal-overlay"
		role="presentation"
		on:click={handleOverlayClick}
		on:keydown={handleKeydown}
		transition:fade={{ duration: 150 }}
	>
		<div
			bind:this={modalElement}
			class="modal modal--{size}"
			role="dialog"
			aria-modal="true"
			aria-labelledby={title ? 'modal-title' : undefined}
			on:click|stopPropagation
			on:keydown|stopPropagation
			transition:scale={{ duration: 150, start: 0.95 }}
		>
			{#if title || closeable}
				<header class="modal__header">
					{#if title}
						<h2 id="modal-title" class="modal__title">{title}</h2>
					{/if}
					{#if closeable}
						<Button
							variant="ghost"
							size="sm"
							iconOnly
							on:click={close}
							aria-label="Close modal"
						>
							<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<path d="M18 6L6 18M6 6l12 12" />
							</svg>
						</Button>
					{/if}
				</header>
			{/if}

			<div class="modal__body">
				<slot />
			</div>

			{#if $$slots.footer}
				<footer class="modal__footer">
					<slot name="footer" />
				</footer>
			{/if}
		</div>
	</div>
{/if}

<style>
	.modal-overlay {
		position: fixed;
		inset: 0;
		z-index: var(--z-modal);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--space-4);
		background-color: rgba(0, 0, 0, 0.5);
		backdrop-filter: blur(2px);
	}

	.modal {
		display: flex;
		flex-direction: column;
		max-height: calc(100vh - var(--space-8));
		background-color: var(--color-bg);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-xl);
		overflow: hidden;
	}

	.modal--sm {
		width: 100%;
		max-width: 400px;
	}

	.modal--md {
		width: 100%;
		max-width: 500px;
	}

	.modal--lg {
		width: 100%;
		max-width: 700px;
	}

	.modal--xl {
		width: 100%;
		max-width: 900px;
	}

	.modal__header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-4);
		padding: var(--space-4) var(--space-6);
		border-bottom: 1px solid var(--color-border-light);
	}

	.modal__title {
		margin: 0;
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
	}

	.modal__body {
		flex: 1;
		padding: var(--space-6);
		overflow-y: auto;
	}

	.modal__footer {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		gap: var(--space-3);
		padding: var(--space-4) var(--space-6);
		border-top: 1px solid var(--color-border-light);
		background-color: var(--color-bg-secondary);
	}
</style>
