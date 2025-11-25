<!--
  Auth Layout
  ragged WebUI v0.7.3

  Minimal layout for authentication pages (no sidebar/header)
-->
<script lang="ts">
	import '../../lib/styles/reset.css';
	import '../../lib/styles/tokens.css';
	import '../../lib/styles/global.css';

	import { onMount } from 'svelte';
	import { theme } from '$stores';

	// Apply theme on mount
	onMount(() => {
		const unsubscribe = theme.subscribe((value) => {
			if (typeof document !== 'undefined') {
				document.documentElement.setAttribute('data-theme', value);
			}
		});

		return () => {
			unsubscribe();
		};
	});
</script>

<svelte:head>
	<meta name="color-scheme" content={$theme === 'dark' ? 'dark' : 'light'} />
</svelte:head>

<slot />
