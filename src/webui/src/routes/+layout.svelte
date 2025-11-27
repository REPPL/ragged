<!--
  Root Layout
  ragged WebUI v0.9.5

  Main application layout with header, sidebar, and content area
-->
<script lang="ts">
	import '../lib/styles/reset.css';
	import '../lib/styles/tokens.css';
	import '../lib/styles/global.css';

	import { onMount } from 'svelte';
	import { theme } from '$stores';
	import Header from '$lib/components/layout/Header.svelte';
	import Sidebar from '$lib/components/layout/Sidebar.svelte';
	import ToastContainer from '$lib/components/layout/ToastContainer.svelte';
	import CommandPalette from '$lib/components/CommandPalette.svelte';
	import { InstallBanner, OfflineIndicator, UpdateBanner } from '$lib/components/pwa';
	import { pwa } from '$lib/stores/pwa';
	import { sidebarOpen, sidebarWidth, isMobile } from '$stores';

	let commandPaletteOpen = false;

	// Apply theme on mount
	onMount(() => {
		const unsubscribe = theme.subscribe((value) => {
			if (typeof document !== 'undefined') {
				document.documentElement.setAttribute('data-theme', value);
			}
		});

		// Initialise PWA
		pwa.init();

		// Check for mobile on mount and resize
		const checkMobile = () => {
			isMobile.set(window.innerWidth < 768);
			if (window.innerWidth < 768) {
				sidebarOpen.set(false);
			}
		};

		checkMobile();
		window.addEventListener('resize', checkMobile);

		return () => {
			unsubscribe();
			window.removeEventListener('resize', checkMobile);
		};
	});

	$: mainStyle = $sidebarOpen && !$isMobile ? `margin-left: ${$sidebarWidth}px` : '';
</script>

<svelte:head>
	<meta name="color-scheme" content={$theme === 'dark' ? 'dark' : 'light'} />
</svelte:head>

<div class="app">
	<OfflineIndicator />
	<InstallBanner />
	<UpdateBanner />

	<Header />

	<div class="app__body">
		<Sidebar />

		<main class="app__main" style={mainStyle}>
			<slot />
		</main>
	</div>

	<ToastContainer />
	<CommandPalette bind:open={commandPaletteOpen} />
</div>

<style>
	.app {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
		min-height: 100dvh;
		background-color: var(--color-bg);
	}

	.app__body {
		display: flex;
		flex: 1;
		padding-top: var(--header-height);
	}

	.app__main {
		flex: 1;
		min-width: 0;
		padding: var(--space-6);
		transition: margin-left var(--transition-normal);
	}

	@media (max-width: 768px) {
		.app__main {
			padding: var(--space-4);
		}
	}

	/* Safe area insets for notched devices */
	@supports (padding: env(safe-area-inset-bottom)) {
		.app {
			padding-left: env(safe-area-inset-left);
			padding-right: env(safe-area-inset-right);
			padding-bottom: env(safe-area-inset-bottom);
		}
	}
</style>
