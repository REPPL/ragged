/**
 * Commands Store
 * ragged WebUI v0.9.1
 *
 * Manages command palette state, recent commands, and persistence
 */

import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';
import { commandRegistry, type Command } from '$lib/commands/registry';

const RECENT_COMMANDS_KEY = 'ragged-recent-commands';
const MAX_RECENT_COMMANDS = 5;

interface RecentCommand {
	id: string;
	timestamp: number;
}

/**
 * Load recent commands from localStorage
 */
function loadRecentCommands(): RecentCommand[] {
	if (!browser) return [];

	try {
		const stored = localStorage.getItem(RECENT_COMMANDS_KEY);
		if (stored) {
			const parsed = JSON.parse(stored) as RecentCommand[];
			// Filter out commands that no longer exist
			return parsed.filter((rc) => commandRegistry.get(rc.id));
		}
	} catch (e) {
		console.warn('Failed to load recent commands:', e);
	}

	return [];
}

/**
 * Save recent commands to localStorage
 */
function saveRecentCommands(recent: RecentCommand[]): void {
	if (!browser) return;

	try {
		localStorage.setItem(RECENT_COMMANDS_KEY, JSON.stringify(recent));
	} catch (e) {
		console.warn('Failed to save recent commands:', e);
	}
}

/**
 * Create the commands store
 */
function createCommandsStore() {
	const recentCommands = writable<RecentCommand[]>(loadRecentCommands());

	// Subscribe to changes and persist
	recentCommands.subscribe((recent) => {
		saveRecentCommands(recent);
	});

	return {
		subscribe: recentCommands.subscribe,

		/**
		 * Record a command as recently used
		 */
		recordUsage(commandId: string): void {
			recentCommands.update((recent) => {
				// Remove if already exists
				const filtered = recent.filter((rc) => rc.id !== commandId);

				// Add to front
				const updated = [
					{ id: commandId, timestamp: Date.now() },
					...filtered
				].slice(0, MAX_RECENT_COMMANDS);

				return updated;
			});
		},

		/**
		 * Clear recent commands
		 */
		clearRecent(): void {
			recentCommands.set([]);
		},

		/**
		 * Get recent commands as full Command objects
		 */
		getRecentCommands(): Command[] {
			const recent = get(recentCommands);
			return recent
				.map((rc) => commandRegistry.get(rc.id))
				.filter((cmd): cmd is Command => cmd !== undefined);
		}
	};
}

export const commandsStore = createCommandsStore();

/**
 * Derived store for recent commands as full Command objects
 */
export const recentCommands = derived(commandsStore, ($store) => {
	// This is a bit of a hack since we can't access the internal state directly
	// We'll need to use the getRecentCommands method instead
	return commandsStore.getRecentCommands();
});

/**
 * Command palette open state
 */
export const commandPaletteOpen = writable(false);

/**
 * Open the command palette
 */
export function openCommandPalette(): void {
	commandPaletteOpen.set(true);
}

/**
 * Close the command palette
 */
export function closeCommandPalette(): void {
	commandPaletteOpen.set(false);
}

/**
 * Toggle the command palette
 */
export function toggleCommandPalette(): void {
	commandPaletteOpen.update((open) => !open);
}
