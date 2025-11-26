<!--
  Tabs Component
  ragged WebUI v0.7.3

  Usage:
  <Tabs bind:active={tab} tabs={[
    { id: 'text', label: 'Text', icon: '📝' },
    { id: 'image', label: 'Image', icon: '🖼️' }
  ]} />
-->
<script lang="ts">
	import type { TabOrientation } from '$types';

	interface Tab {
		id: string;
		label: string;
		icon?: string;
		disabled?: boolean;
	}

	export let tabs: Tab[] = [];
	export let active = tabs[0]?.id || '';
	export let orientation: TabOrientation = 'horizontal';
	export let variant: 'default' | 'pill' | 'underline' = 'default';

	function handleKeydown(event: KeyboardEvent, index: number) {
		const enabledTabs = tabs.filter(t => !t.disabled);
		const currentIndex = enabledTabs.findIndex(t => t.id === active);

		let newIndex = currentIndex;

		switch (event.key) {
			case 'ArrowRight':
			case 'ArrowDown':
				event.preventDefault();
				newIndex = (currentIndex + 1) % enabledTabs.length;
				break;
			case 'ArrowLeft':
			case 'ArrowUp':
				event.preventDefault();
				newIndex = (currentIndex - 1 + enabledTabs.length) % enabledTabs.length;
				break;
			case 'Home':
				event.preventDefault();
				newIndex = 0;
				break;
			case 'End':
				event.preventDefault();
				newIndex = enabledTabs.length - 1;
				break;
		}

		if (newIndex !== currentIndex) {
			active = enabledTabs[newIndex].id;
		}
	}
</script>

<div
	class="tabs tabs--{orientation} tabs--{variant}"
	role="tablist"
	aria-orientation={orientation}
>
	{#each tabs as tab, index (tab.id)}
		<button
			role="tab"
			type="button"
			id="tab-{tab.id}"
			class="tabs__tab"
			class:tabs__tab--active={active === tab.id}
			aria-selected={active === tab.id}
			aria-controls="panel-{tab.id}"
			tabindex={active === tab.id ? 0 : -1}
			disabled={tab.disabled}
			on:click={() => !tab.disabled && (active = tab.id)}
			on:keydown={(e) => handleKeydown(e, index)}
		>
			{#if tab.icon}
				<span class="tabs__icon" aria-hidden="true">{tab.icon}</span>
			{/if}
			<span class="tabs__label">{tab.label}</span>
		</button>
	{/each}
</div>

<style>
	.tabs {
		display: flex;
		gap: var(--space-1);
	}

	.tabs--horizontal {
		flex-direction: row;
	}

	.tabs--vertical {
		flex-direction: column;
	}

	.tabs__tab {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-2);
		padding: var(--space-2) var(--space-4);
		font-family: var(--font-sans);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-secondary);
		background: none;
		border: none;
		cursor: pointer;
		transition:
			color var(--transition-fast),
			background-color var(--transition-fast),
			border-color var(--transition-fast);
		white-space: nowrap;
	}

	.tabs__tab:hover:not(:disabled) {
		color: var(--color-text-primary);
	}

	.tabs__tab:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.tabs__tab:focus-visible {
		outline: none;
		box-shadow: var(--shadow-focus);
	}

	/* Default variant */
	.tabs--default .tabs__tab {
		border-radius: var(--radius-md);
	}

	.tabs--default .tabs__tab--active {
		color: var(--color-text-inverse);
		background-color: var(--color-primary);
	}

	.tabs--default .tabs__tab--active:hover:not(:disabled) {
		color: var(--color-text-inverse);
	}

	/* Pill variant */
	.tabs--pill {
		padding: var(--space-1);
		background-color: var(--color-bg-secondary);
		border-radius: var(--radius-lg);
	}

	.tabs--pill .tabs__tab {
		border-radius: var(--radius-md);
	}

	.tabs--pill .tabs__tab--active {
		color: var(--color-text-primary);
		background-color: var(--color-bg);
		box-shadow: var(--shadow-sm);
	}

	/* Underline variant */
	.tabs--underline {
		border-bottom: 1px solid var(--color-border-light);
	}

	.tabs--underline .tabs__tab {
		padding: var(--space-3) var(--space-4);
		margin-bottom: -1px;
		border-bottom: 2px solid transparent;
		border-radius: 0;
	}

	.tabs--underline .tabs__tab--active {
		color: var(--color-primary);
		border-bottom-color: var(--color-primary);
	}

	.tabs__icon {
		font-size: 1.1em;
	}
</style>
