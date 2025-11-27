<!--
  Install Banner Component
  ragged WebUI v0.9.5

  PWA installation prompt banner
-->
<script lang="ts">
	import { pwa, isInstallable, isInstalled } from '$lib/stores/pwa';
	import Button from '../Button.svelte';

	let dismissed = false;

	$: showBanner = $isInstallable && !$isInstalled && !dismissed;

	async function handleInstall() {
		const success = await pwa.install();
		if (!success) {
			dismissed = true;
		}
	}

	function handleDismiss() {
		dismissed = true;
	}
</script>

{#if showBanner}
	<div class="install-banner" role="alert">
		<div class="install-banner__content">
			<div class="install-banner__icon">
				<svg
					width="24"
					height="24"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
				>
					<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" />
				</svg>
			</div>
			<div class="install-banner__text">
				<strong>Install ragged</strong>
				<span>Add to home screen for quick access and offline use</span>
			</div>
		</div>

		<div class="install-banner__actions">
			<Button variant="ghost" size="sm" on:click={handleDismiss}>
				Not now
			</Button>
			<Button variant="primary" size="sm" on:click={handleInstall}>
				Install
			</Button>
		</div>
	</div>
{/if}

<style>
	.install-banner {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-4);
		padding: var(--space-3) var(--space-4);
		background-color: var(--color-primary);
		color: white;
		animation: slideDown 0.3s ease-out;
	}

	@keyframes slideDown {
		from {
			transform: translateY(-100%);
			opacity: 0;
		}
		to {
			transform: translateY(0);
			opacity: 1;
		}
	}

	.install-banner__content {
		display: flex;
		align-items: center;
		gap: var(--space-3);
	}

	.install-banner__icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		background-color: rgba(255, 255, 255, 0.2);
		border-radius: var(--radius-md);
	}

	.install-banner__text {
		display: flex;
		flex-direction: column;
	}

	.install-banner__text strong {
		font-weight: var(--font-weight-semibold);
	}

	.install-banner__text span {
		font-size: var(--font-size-sm);
		opacity: 0.9;
	}

	.install-banner__actions {
		display: flex;
		align-items: center;
		gap: var(--space-2);
	}

	@media (max-width: 640px) {
		.install-banner {
			flex-direction: column;
			align-items: stretch;
			text-align: center;
		}

		.install-banner__content {
			flex-direction: column;
		}

		.install-banner__actions {
			justify-content: center;
		}
	}
</style>
