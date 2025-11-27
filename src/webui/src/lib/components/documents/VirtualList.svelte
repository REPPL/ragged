<!--
  Virtual List Component
  ragged WebUI v0.9.2

  Efficient rendering of large lists using windowing
  Only renders visible items plus a buffer zone
-->
<script lang="ts">
	import { onMount, onDestroy, tick } from 'svelte';

	type T = $$Generic;

	export let items: T[] = [];
	export let itemHeight = 80;
	export let bufferSize = 5;
	export let keyFn: (item: T) => string = (item) => String(item);

	let container: HTMLDivElement;
	let scrollTop = 0;
	let containerHeight = 0;

	$: totalHeight = items.length * itemHeight;
	$: startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - bufferSize);
	$: visibleCount = Math.ceil(containerHeight / itemHeight) + bufferSize * 2;
	$: endIndex = Math.min(items.length, startIndex + visibleCount);
	$: visibleItems = items.slice(startIndex, endIndex);
	$: offsetY = startIndex * itemHeight;

	function handleScroll() {
		if (container) {
			scrollTop = container.scrollTop;
		}
	}

	function handleResize() {
		if (container) {
			containerHeight = container.clientHeight;
		}
	}

	let resizeObserver: ResizeObserver | null = null;

	onMount(() => {
		if (container) {
			containerHeight = container.clientHeight;

			resizeObserver = new ResizeObserver(() => {
				handleResize();
			});
			resizeObserver.observe(container);
		}
	});

	onDestroy(() => {
		if (resizeObserver) {
			resizeObserver.disconnect();
		}
	});

	export function scrollToIndex(index: number, behavior: ScrollBehavior = 'smooth') {
		if (container && index >= 0 && index < items.length) {
			const targetTop = index * itemHeight;
			container.scrollTo({ top: targetTop, behavior });
		}
	}

	export function scrollToTop(behavior: ScrollBehavior = 'smooth') {
		if (container) {
			container.scrollTo({ top: 0, behavior });
		}
	}
</script>

<div
	bind:this={container}
	class="virtual-list"
	on:scroll={handleScroll}
	role="list"
>
	<div class="virtual-list__spacer" style="height: {totalHeight}px">
		<div class="virtual-list__content" style="transform: translateY({offsetY}px)">
			{#each visibleItems as item, index (keyFn(item))}
				<div class="virtual-list__item" style="height: {itemHeight}px" role="listitem">
					<slot {item} index={startIndex + index} />
				</div>
			{/each}
		</div>
	</div>
</div>

<style>
	.virtual-list {
		flex: 1;
		overflow-y: auto;
		overflow-x: hidden;
	}

	.virtual-list__spacer {
		position: relative;
		width: 100%;
	}

	.virtual-list__content {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		will-change: transform;
	}

	.virtual-list__item {
		box-sizing: border-box;
	}
</style>
