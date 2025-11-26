<!--
  Skeleton Component
  ragged WebUI v0.7.3

  Usage:
  <Skeleton width="200px" height="20px" />
  <Skeleton circle size="40px" />
-->
<script lang="ts">
	export let width: string = '100%';
	export let height: string = '20px';
	export let circle = false;
	export let size: string | undefined = undefined;
	export let rounded: 'none' | 'sm' | 'md' | 'lg' | 'full' = 'md';

	$: computedWidth = circle && size ? size : width;
	$: computedHeight = circle && size ? size : height;
	$: borderRadius = circle ? 'var(--radius-full)'
		: rounded === 'none' ? '0'
		: rounded === 'sm' ? 'var(--radius-sm)'
		: rounded === 'md' ? 'var(--radius-md)'
		: rounded === 'lg' ? 'var(--radius-lg)'
		: 'var(--radius-full)';
</script>

<div
	class="skeleton"
	style:width={computedWidth}
	style:height={computedHeight}
	style:border-radius={borderRadius}
	aria-hidden="true"
	{...$$restProps}
/>

<style>
	.skeleton {
		background: linear-gradient(
			90deg,
			var(--color-bg-secondary) 0%,
			var(--color-bg-tertiary) 50%,
			var(--color-bg-secondary) 100%
		);
		background-size: 200% 100%;
		animation: shimmer 1.5s ease-in-out infinite;
	}

	@keyframes shimmer {
		0% {
			background-position: 200% 0;
		}
		100% {
			background-position: -200% 0;
		}
	}
</style>
