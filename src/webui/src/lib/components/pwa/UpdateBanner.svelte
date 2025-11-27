<!--
  Update Banner Component
  ragged WebUI v0.9.5

  Shows when a new version is available
-->
<script lang="ts">
	import { pwa, isUpdateAvailable } from '$lib/stores/pwa';
	import Button from '../Button.svelte';
	import { slide } from 'svelte/transition';

	let dismissed = false;

	$: showBanner = $isUpdateAvailable && !dismissed;

	function handleUpdate() {
		pwa.update();
	}

	function handleDismiss() {
		dismissed = true;
	}
</script>

{#if showBanner}
	<div
		class="update-banner"
		role="alert"
		transition:slide={{ duration: 200 }}
	>
		<div class="update-banner__content">
			<svg
				width="20"
				height="20"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
			>
				<polyline points="23 4 23 10 17 10" />
				<polyline points="1 20 1 14 7 14" />
				<path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
			</svg>
			<span>A new version is available</span>
		</div>

		<div class="update-banner__actions">
			<Button variant="ghost" size="sm" on:click={handleDismiss}>
				Later
			</Button>
			<Button variant="secondary" size="sm" on:click={handleUpdate}>
				Update now
			</Button>
		</div>
	</div>
{/if}

<style>
	.update-banner {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-4);
		padding: var(--space-3) var(--space-4);
		background-color: var(--color-success);
		color: white;
	}

	.update-banner__content {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
	}

	.update-banner__actions {
		display: flex;
		align-items: center;
		gap: var(--space-2);
	}

	@media (max-width: 640px) {
		.update-banner {
			flex-direction: column;
			align-items: stretch;
		}

		.update-banner__actions {
			justify-content: flex-end;
		}
	}
</style>
