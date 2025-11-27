<!--
  Header Component
  ragged WebUI v0.9.3

  Main application header (72px height from design)
-->
<script lang="ts">
	import { sidebar, themeMode, resolvedTheme } from '$stores';
	import Button from '../Button.svelte';

	export let showSidebarToggle = true;

	function toggleTheme() {
		themeMode.toggle();
	}

	function toggleSidebar() {
		sidebar.toggle();
	}

	$: themeIcon = $resolvedTheme === 'dark' ? '☀️' : '🌙';
	$: themeLabel = $resolvedTheme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
</script>

<header class="header">
	<div class="header__left">
		{#if showSidebarToggle}
			<Button
				variant="ghost"
				size="sm"
				iconOnly
				on:click={toggleSidebar}
				aria-label="Toggle sidebar"
				aria-expanded={$sidebar.isOpen}
			>
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M3 12h18M3 6h18M3 18h18" />
				</svg>
			</Button>
		{/if}

		<a href="/" class="header__logo">
			<span class="header__title">ragged</span>
			<span class="header__tagline">privacy-first RAG</span>
		</a>
	</div>

	<nav class="header__nav">
		<a href="/" class="header__link" aria-current={undefined}>Query</a>
		<a href="/documents" class="header__link">Documents</a>
		<a href="/graph" class="header__link">Graph</a>
		<a href="/analytics" class="header__link">Analytics</a>
	</nav>

	<div class="header__right">
		<Button
			variant="ghost"
			size="sm"
			iconOnly
			on:click={toggleTheme}
			aria-label={themeLabel}
		>
			<span aria-hidden="true">{themeIcon}</span>
		</Button>

		<Button
			variant="ghost"
			size="sm"
			iconOnly
			aria-label="Settings"
		>
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<circle cx="12" cy="12" r="3" />
				<path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z" />
			</svg>
		</Button>
	</div>
</header>

<style>
	.header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		height: var(--header-height);
		padding: 0 var(--space-4);
		background-color: var(--color-bg);
		border-bottom: 1px solid var(--color-border-light);
		position: sticky;
		top: 0;
		z-index: var(--z-sticky);
	}

	.header__left {
		display: flex;
		align-items: center;
		gap: var(--space-3);
	}

	.header__logo {
		display: flex;
		align-items: baseline;
		gap: var(--space-2);
		text-decoration: none;
		color: inherit;
	}

	.header__title {
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-text-primary);
	}

	.header__tagline {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.header__nav {
		display: flex;
		align-items: center;
		gap: var(--space-1);
	}

	.header__link {
		padding: var(--space-2) var(--space-3);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-secondary);
		text-decoration: none;
		border-radius: var(--radius-md);
		transition: color var(--transition-fast), background-color var(--transition-fast);
	}

	.header__link:hover {
		color: var(--color-text-primary);
		background-color: var(--color-bg-secondary);
		text-decoration: none;
	}

	.header__link[aria-current='page'] {
		color: var(--color-primary);
		background-color: var(--color-primary-light);
	}

	.header__right {
		display: flex;
		align-items: center;
		gap: var(--space-1);
	}

	@media (max-width: 767px) {
		.header__tagline {
			display: none;
		}

		.header__nav {
			display: none;
		}
	}
</style>
