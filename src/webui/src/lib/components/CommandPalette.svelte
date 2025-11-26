<!--
  Command Palette Component
  ragged WebUI v0.7.3

  Quick command access with keyboard navigation (Cmd+K)
-->
<script lang="ts">
	import { createEventDispatcher, onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import type { CommandPaletteItem } from '$types';

	export let open = false;

	const dispatch = createEventDispatcher<{
		close: void;
	}>();

	let searchInput: HTMLInputElement;
	let searchQuery = '';
	let selectedIndex = 0;

	// Default commands
	const defaultCommands: CommandPaletteItem[] = [
		{
			id: 'nav-query',
			label: 'Go to Query',
			description: 'Search your documents',
			icon: '🔍',
			shortcut: 'G Q',
			category: 'Navigation',
			action: () => goto('/')
		},
		{
			id: 'nav-documents',
			label: 'Go to Documents',
			description: 'Manage your documents',
			icon: '📄',
			shortcut: 'G D',
			category: 'Navigation',
			action: () => goto('/documents')
		},
		{
			id: 'nav-collections',
			label: 'Go to Collections',
			description: 'Organise your collections',
			icon: '📁',
			shortcut: 'G C',
			category: 'Navigation',
			action: () => goto('/collections')
		},
		{
			id: 'nav-history',
			label: 'Go to History',
			description: 'View query history',
			icon: '🕐',
			shortcut: 'G H',
			category: 'Navigation',
			action: () => goto('/history')
		},
		{
			id: 'nav-analytics',
			label: 'Go to Analytics',
			description: 'View system analytics',
			icon: '📊',
			shortcut: 'G A',
			category: 'Navigation',
			action: () => goto('/analytics')
		},
		{
			id: 'nav-settings',
			label: 'Go to Settings',
			description: 'Configure preferences',
			icon: '⚙️',
			shortcut: 'G S',
			category: 'Navigation',
			action: () => goto('/settings')
		},
		{
			id: 'action-upload',
			label: 'Upload Document',
			description: 'Upload a new document',
			icon: '📤',
			shortcut: 'U',
			category: 'Actions',
			action: () => goto('/documents')
		},
		{
			id: 'action-new-collection',
			label: 'Create Collection',
			description: 'Create a new collection',
			icon: '➕',
			shortcut: 'N C',
			category: 'Actions',
			action: () => goto('/collections')
		}
	];

	$: filteredCommands = searchQuery
		? defaultCommands.filter(
				(cmd) =>
					cmd.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
					cmd.description?.toLowerCase().includes(searchQuery.toLowerCase())
			)
		: defaultCommands;

	$: groupedCommands = filteredCommands.reduce(
		(acc, cmd) => {
			const category = cmd.category || 'Other';
			if (!acc[category]) acc[category] = [];
			acc[category].push(cmd);
			return acc;
		},
		{} as Record<string, CommandPaletteItem[]>
	);

	$: if (selectedIndex >= filteredCommands.length) {
		selectedIndex = Math.max(0, filteredCommands.length - 1);
	}

	function handleKeydown(event: KeyboardEvent) {
		if (!open) return;

		switch (event.key) {
			case 'Escape':
				event.preventDefault();
				close();
				break;
			case 'ArrowDown':
				event.preventDefault();
				selectedIndex = Math.min(selectedIndex + 1, filteredCommands.length - 1);
				break;
			case 'ArrowUp':
				event.preventDefault();
				selectedIndex = Math.max(selectedIndex - 1, 0);
				break;
			case 'Enter':
				event.preventDefault();
				if (filteredCommands[selectedIndex]) {
					executeCommand(filteredCommands[selectedIndex]);
				}
				break;
		}
	}

	function handleGlobalKeydown(event: KeyboardEvent) {
		// Open command palette with Cmd+K
		if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
			event.preventDefault();
			open = !open;
			if (open) {
				setTimeout(() => searchInput?.focus(), 0);
			}
		}
	}

	function executeCommand(command: CommandPaletteItem) {
		command.action();
		close();
	}

	function close() {
		open = false;
		searchQuery = '';
		selectedIndex = 0;
		dispatch('close');
	}

	function handleOverlayClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			close();
		}
	}

	onMount(() => {
		window.addEventListener('keydown', handleGlobalKeydown);
	});

	onDestroy(() => {
		window.removeEventListener('keydown', handleGlobalKeydown);
	});

	$: if (open && searchInput) {
		searchInput.focus();
	}
</script>

{#if open}
	<div
		class="command-palette__overlay"
		on:click={handleOverlayClick}
		on:keydown={handleKeydown}
		role="dialog"
		aria-modal="true"
		aria-label="Command palette"
	>
		<div class="command-palette">
			<div class="command-palette__search">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<circle cx="11" cy="11" r="8" />
					<path d="M21 21l-4.35-4.35" />
				</svg>
				<input
					bind:this={searchInput}
					bind:value={searchQuery}
					type="text"
					class="command-palette__input"
					placeholder="Search commands..."
					autocomplete="off"
					spellcheck="false"
				/>
				<kbd class="command-palette__shortcut">ESC</kbd>
			</div>

			<div class="command-palette__results">
				{#if filteredCommands.length === 0}
					<p class="command-palette__empty">No commands found</p>
				{:else}
					{#each Object.entries(groupedCommands) as [category, commands]}
						<div class="command-palette__group">
							<p class="command-palette__category">{category}</p>
							{#each commands as command, index}
								{@const globalIndex = filteredCommands.indexOf(command)}
								<button
									type="button"
									class="command-palette__item"
									class:command-palette__item--selected={globalIndex === selectedIndex}
									on:click={() => executeCommand(command)}
									on:mouseenter={() => (selectedIndex = globalIndex)}
								>
									<span class="command-palette__icon">{command.icon}</span>
									<div class="command-palette__item-content">
										<span class="command-palette__label">{command.label}</span>
										{#if command.description}
											<span class="command-palette__description">{command.description}</span>
										{/if}
									</div>
									{#if command.shortcut}
										<kbd class="command-palette__item-shortcut">{command.shortcut}</kbd>
									{/if}
								</button>
							{/each}
						</div>
					{/each}
				{/if}
			</div>

			<div class="command-palette__footer">
				<span class="command-palette__hint">
					<kbd>↑</kbd><kbd>↓</kbd> to navigate
				</span>
				<span class="command-palette__hint">
					<kbd>↵</kbd> to select
				</span>
				<span class="command-palette__hint">
					<kbd>esc</kbd> to close
				</span>
			</div>
		</div>
	</div>
{/if}

<style>
	.command-palette__overlay {
		position: fixed;
		inset: 0;
		display: flex;
		align-items: flex-start;
		justify-content: center;
		padding-top: 15vh;
		background-color: rgba(0, 0, 0, 0.5);
		z-index: var(--z-modal);
		animation: fadeIn var(--transition-fast) ease-out;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	.command-palette {
		width: 100%;
		max-width: 600px;
		max-height: 70vh;
		display: flex;
		flex-direction: column;
		background-color: var(--color-bg);
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-2xl);
		overflow: hidden;
		animation: slideIn var(--transition-fast) ease-out;
	}

	@keyframes slideIn {
		from {
			opacity: 0;
			transform: translateY(-20px) scale(0.95);
		}
		to {
			opacity: 1;
			transform: translateY(0) scale(1);
		}
	}

	.command-palette__search {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		padding: var(--space-4);
		border-bottom: 1px solid var(--color-border-light);
	}

	.command-palette__search svg {
		color: var(--color-text-muted);
		flex-shrink: 0;
	}

	.command-palette__input {
		flex: 1;
		font-size: var(--font-size-lg);
		color: var(--color-text-primary);
		background: none;
		border: none;
		outline: none;
	}

	.command-palette__input::placeholder {
		color: var(--color-text-muted);
	}

	.command-palette__shortcut {
		padding: var(--space-1) var(--space-2);
		font-size: var(--font-size-xs);
		font-family: var(--font-mono);
		color: var(--color-text-muted);
		background-color: var(--color-bg-tertiary);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-sm);
	}

	.command-palette__results {
		flex: 1;
		overflow-y: auto;
		padding: var(--space-2);
	}

	.command-palette__empty {
		padding: var(--space-8);
		text-align: center;
		color: var(--color-text-muted);
	}

	.command-palette__group {
		margin-bottom: var(--space-3);
	}

	.command-palette__category {
		padding: var(--space-2) var(--space-3);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.command-palette__item {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		width: 100%;
		padding: var(--space-3);
		text-align: left;
		background: none;
		border: none;
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: background-color var(--transition-fast);
	}

	.command-palette__item:hover,
	.command-palette__item--selected {
		background-color: var(--color-bg-secondary);
	}

	.command-palette__icon {
		font-size: var(--font-size-lg);
		flex-shrink: 0;
	}

	.command-palette__item-content {
		flex: 1;
		min-width: 0;
	}

	.command-palette__label {
		display: block;
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-primary);
	}

	.command-palette__description {
		display: block;
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.command-palette__item-shortcut {
		padding: var(--space-1) var(--space-2);
		font-size: var(--font-size-xs);
		font-family: var(--font-mono);
		color: var(--color-text-muted);
		background-color: var(--color-bg-tertiary);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-sm);
	}

	.command-palette__footer {
		display: flex;
		gap: var(--space-4);
		padding: var(--space-3) var(--space-4);
		border-top: 1px solid var(--color-border-light);
		background-color: var(--color-bg-secondary);
	}

	.command-palette__hint {
		display: flex;
		align-items: center;
		gap: var(--space-1);
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.command-palette__hint kbd {
		padding: 2px 6px;
		font-family: var(--font-mono);
		font-size: var(--font-size-xs);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-sm);
	}

	@media (max-width: 640px) {
		.command-palette__overlay {
			padding: var(--space-4);
			align-items: flex-start;
		}

		.command-palette {
			max-height: 80vh;
		}
	}
</style>
