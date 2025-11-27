<!--
  Command Palette Component
  ragged WebUI v0.9.1

  Quick command access with fuzzy search and keyboard navigation (Cmd+K)
  Features:
  - Fuzzy search with Fuse.js
  - Recent commands persistence
  - Category grouping
  - Keyboard navigation
-->
<script lang="ts">
	import { createEventDispatcher, onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import {
		commandRegistry,
		createCommandSearch,
		searchCommands,
		highlightMatches,
		getMatchIndices,
		type Command,
		type SearchResult
	} from '$lib/commands';
	import { commandsStore, commandPaletteOpen, closeCommandPalette } from '$stores';
	import type Fuse from 'fuse.js';

	const dispatch = createEventDispatcher<{
		close: void;
	}>();

	let searchInput: HTMLInputElement;
	let searchQuery = '';
	let selectedIndex = 0;
	let fuse: Fuse<Command> | null = null;

	// Reactive commands list
	$: allCommands = commandRegistry.getAll();
	$: recentCommands = commandsStore.getRecentCommands();

	// Create fuse instance when commands change
	$: if (allCommands.length > 0) {
		fuse = createCommandSearch(allCommands);
	}

	// Search results
	$: searchResults = searchQuery && fuse
		? searchCommands(fuse, searchQuery, { limit: 15, threshold: 0.5 })
		: [];

	// Display commands: search results, recent commands, or all commands
	$: displayCommands = searchQuery
		? searchResults.map((r) => r.item)
		: recentCommands.length > 0
			? [...recentCommands, ...allCommands.filter((c) => !recentCommands.some((r) => r.id === c.id))]
			: allCommands;

	// Group commands by category
	$: groupedCommands = (() => {
		const groups: Record<string, { commands: Command[]; results?: SearchResult[] }> = {};

		// Add recent commands group if showing recent
		if (!searchQuery && recentCommands.length > 0) {
			groups['Recent'] = { commands: recentCommands };
		}

		// Group remaining commands
		const commandsToGroup = searchQuery
			? searchResults.map((r) => ({ ...r.item, _searchResult: r }))
			: allCommands.filter((c) => !recentCommands.some((r) => r.id === c.id));

		for (const cmd of commandsToGroup) {
			const category = cmd.category || 'Other';
			if (!groups[category]) {
				groups[category] = { commands: [] };
			}
			groups[category].commands.push(cmd);
		}

		return groups;
	})();

	// Flatten for keyboard navigation
	$: flattenedCommands = displayCommands;

	// Keep selected index in bounds
	$: if (selectedIndex >= flattenedCommands.length) {
		selectedIndex = Math.max(0, flattenedCommands.length - 1);
	}

	// Get search result for a command (for highlighting)
	function getSearchResult(commandId: string): SearchResult | undefined {
		return searchResults.find((r) => r.item.id === commandId);
	}

	function handleKeydown(event: KeyboardEvent) {
		if (!$commandPaletteOpen) return;

		switch (event.key) {
			case 'Escape':
				event.preventDefault();
				close();
				break;
			case 'ArrowDown':
				event.preventDefault();
				selectedIndex = Math.min(selectedIndex + 1, flattenedCommands.length - 1);
				scrollToSelected();
				break;
			case 'ArrowUp':
				event.preventDefault();
				selectedIndex = Math.max(selectedIndex - 1, 0);
				scrollToSelected();
				break;
			case 'Enter':
				event.preventDefault();
				if (flattenedCommands[selectedIndex]) {
					executeCommand(flattenedCommands[selectedIndex]);
				}
				break;
			case 'Tab':
				event.preventDefault();
				if (event.shiftKey) {
					selectedIndex = Math.max(selectedIndex - 1, 0);
				} else {
					selectedIndex = Math.min(selectedIndex + 1, flattenedCommands.length - 1);
				}
				scrollToSelected();
				break;
		}
	}

	function handleGlobalKeydown(event: KeyboardEvent) {
		// Open command palette with Cmd+K or Ctrl+K
		if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
			event.preventDefault();
			if ($commandPaletteOpen) {
				close();
			} else {
				commandPaletteOpen.set(true);
				setTimeout(() => searchInput?.focus(), 0);
			}
		}
	}

	function scrollToSelected() {
		const selected = document.querySelector('.command-palette__item--selected');
		selected?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
	}

	function executeCommand(command: Command) {
		// Record usage for recent commands
		commandsStore.recordUsage(command.id);

		// Execute the command
		command.action();
		close();
	}

	function close() {
		closeCommandPalette();
		searchQuery = '';
		selectedIndex = 0;
		dispatch('close');
	}

	function handleOverlayClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			close();
		}
	}

	// Icon mapping for Lucide icons
	const iconMap: Record<string, string> = {
		search: 'M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z',
		'file-text': 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8',
		folder: 'M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z',
		'folder-plus': 'M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2zM12 11v6M9 14h6',
		clock: 'M12 22a10 10 0 100-20 10 10 0 000 20zM12 6v6l4 2',
		'bar-chart-2': 'M18 20V10M12 20V4M6 20v-6',
		settings: 'M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z',
		upload: 'M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12',
		sun: 'M12 17a5 5 0 100-10 5 5 0 000 10zM12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42',
		moon: 'M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z',
		contrast: 'M12 22a10 10 0 100-20 10 10 0 000 20zM12 2v20',
		keyboard: 'M20 4H4a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V6a2 2 0 00-2-2zM6 8h2M10 8h2M14 8h2M18 8h2M6 12h2M10 12h8M6 16h12',
		'book-open': 'M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2zM22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z'
	};

	function getIconPath(iconName: string): string {
		return iconMap[iconName] || iconMap.search;
	}

	onMount(() => {
		window.addEventListener('keydown', handleGlobalKeydown);
	});

	onDestroy(() => {
		window.removeEventListener('keydown', handleGlobalKeydown);
	});

	// Focus input when opened
	$: if ($commandPaletteOpen && searchInput) {
		setTimeout(() => searchInput?.focus(), 0);
	}
</script>

{#if $commandPaletteOpen}
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
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
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
					aria-label="Search commands"
				/>
				<kbd class="command-palette__shortcut">ESC</kbd>
			</div>

			<div class="command-palette__results" role="listbox" aria-label="Commands">
				{#if flattenedCommands.length === 0}
					<p class="command-palette__empty">No commands found for "{searchQuery}"</p>
				{:else}
					{#each Object.entries(groupedCommands) as [category, { commands }]}
						{#if commands.length > 0}
							<div class="command-palette__group">
								<p class="command-palette__category">{category}</p>
								{#each commands as command}
									{@const globalIndex = flattenedCommands.indexOf(command)}
									{@const searchResult = getSearchResult(command.id)}
									{@const labelMatches = searchResult ? getMatchIndices(searchResult.matches, 'label') : undefined}
									<button
										type="button"
										class="command-palette__item"
										class:command-palette__item--selected={globalIndex === selectedIndex}
										on:click={() => executeCommand(command)}
										on:mouseenter={() => (selectedIndex = globalIndex)}
										role="option"
										aria-selected={globalIndex === selectedIndex}
									>
										<span class="command-palette__icon">
											{#if command.icon && iconMap[command.icon]}
												<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
													<path d={getIconPath(command.icon)} />
												</svg>
											{:else}
												<span class="command-palette__icon-emoji">{command.icon || '⚡'}</span>
											{/if}
										</span>
										<div class="command-palette__item-content">
											<span class="command-palette__label">
												{#if labelMatches}
													{#each highlightMatches(command.label, labelMatches) as segment}
														{#if segment.highlight}
															<mark class="command-palette__highlight">{segment.text}</mark>
														{:else}
															{segment.text}
														{/if}
													{/each}
												{:else}
													{command.label}
												{/if}
											</span>
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
						{/if}
					{/each}
				{/if}
			</div>

			<div class="command-palette__footer">
				<span class="command-palette__hint">
					<kbd>↑</kbd><kbd>↓</kbd> navigate
				</span>
				<span class="command-palette__hint">
					<kbd>↵</kbd> select
				</span>
				<span class="command-palette__hint">
					<kbd>esc</kbd> close
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
		backdrop-filter: blur(4px);
		z-index: var(--z-modal);
		animation: fadeIn var(--transition-fast) ease-out;
	}

	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}

	.command-palette {
		width: 100%;
		max-width: 600px;
		max-height: 70vh;
		display: flex;
		flex-direction: column;
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
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

	.command-palette__group:last-child {
		margin-bottom: 0;
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

	.command-palette__item--selected {
		outline: 2px solid var(--color-primary);
		outline-offset: -2px;
	}

	.command-palette__icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		flex-shrink: 0;
		color: var(--color-text-secondary);
	}

	.command-palette__icon-emoji {
		font-size: var(--font-size-lg);
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

	.command-palette__highlight {
		background-color: var(--color-warning-light);
		color: inherit;
		font-weight: var(--font-weight-bold);
		border-radius: 2px;
		padding: 0 2px;
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
