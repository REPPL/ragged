<!--
  Offline Indicator Component
  ragged WebUI v0.9.5

  Shows connectivity status when offline
-->
<script lang="ts">
	import { isOnline } from '$lib/stores/pwa';
	import { fade, slide } from 'svelte/transition';
</script>

{#if !$isOnline}
	<div
		class="offline-indicator"
		role="status"
		aria-live="polite"
		transition:slide={{ duration: 200 }}
	>
		<svg
			width="16"
			height="16"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="2"
		>
			<line x1="1" y1="1" x2="23" y2="23" />
			<path d="M16.72 11.06A10.94 10.94 0 0119 12.55M5 12.55a10.94 10.94 0 015.17-2.39" />
			<path d="M10.71 5.05A16 16 0 0122.58 9M1.42 9a15.91 15.91 0 014.7-2.88" />
			<path d="M8.53 16.11a6 6 0 016.95 0M12 20h.01" />
		</svg>
		<span>You're offline</span>
	</div>
{/if}

<style>
	.offline-indicator {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-2);
		padding: var(--space-2) var(--space-4);
		background-color: var(--color-warning);
		color: var(--color-text-inverse);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
	}
</style>
