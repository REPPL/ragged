/**
 * Command Registry
 * ragged WebUI v0.9.1
 *
 * Extensible command registry for the command palette
 * Supports dynamic command registration and context-aware filtering
 */

import { goto } from '$app/navigation';

export interface Command {
	id: string;
	label: string;
	description?: string;
	icon?: string;
	shortcut?: string;
	category: CommandCategory;
	keywords?: string[];
	action: () => void | Promise<void>;
	/** Optional context check - return false to hide command */
	when?: () => boolean;
	/** Priority for sorting (higher = more important) */
	priority?: number;
}

export type CommandCategory =
	| 'Navigation'
	| 'Actions'
	| 'Documents'
	| 'Collections'
	| 'Query'
	| 'Settings'
	| 'Help';

export interface CommandRegistryOptions {
	/** Current route path for context-aware filtering */
	currentPath?: string;
}

class CommandRegistry {
	private commands: Map<string, Command> = new Map();
	private listeners: Set<() => void> = new Set();

	constructor() {
		this.registerDefaultCommands();
	}

	/**
	 * Register a command
	 */
	register(command: Command): void {
		this.commands.set(command.id, command);
		this.notifyListeners();
	}

	/**
	 * Register multiple commands
	 */
	registerAll(commands: Command[]): void {
		commands.forEach((cmd) => this.commands.set(cmd.id, cmd));
		this.notifyListeners();
	}

	/**
	 * Unregister a command
	 */
	unregister(id: string): void {
		this.commands.delete(id);
		this.notifyListeners();
	}

	/**
	 * Get a command by ID
	 */
	get(id: string): Command | undefined {
		return this.commands.get(id);
	}

	/**
	 * Get all commands, optionally filtered by context
	 */
	getAll(options?: CommandRegistryOptions): Command[] {
		const commands = Array.from(this.commands.values());

		// Filter by context
		const filtered = commands.filter((cmd) => {
			if (cmd.when && !cmd.when()) {
				return false;
			}
			return true;
		});

		// Sort by priority (descending) then alphabetically
		return filtered.sort((a, b) => {
			const priorityDiff = (b.priority ?? 0) - (a.priority ?? 0);
			if (priorityDiff !== 0) return priorityDiff;
			return a.label.localeCompare(b.label);
		});
	}

	/**
	 * Get commands grouped by category
	 */
	getGrouped(options?: CommandRegistryOptions): Record<CommandCategory, Command[]> {
		const commands = this.getAll(options);
		const grouped: Partial<Record<CommandCategory, Command[]>> = {};

		for (const cmd of commands) {
			if (!grouped[cmd.category]) {
				grouped[cmd.category] = [];
			}
			grouped[cmd.category]!.push(cmd);
		}

		return grouped as Record<CommandCategory, Command[]>;
	}

	/**
	 * Subscribe to registry changes
	 */
	subscribe(listener: () => void): () => void {
		this.listeners.add(listener);
		return () => this.listeners.delete(listener);
	}

	private notifyListeners(): void {
		this.listeners.forEach((listener) => listener());
	}

	private registerDefaultCommands(): void {
		// Navigation commands
		this.registerAll([
			{
				id: 'nav-query',
				label: 'Go to Query',
				description: 'Search your documents',
				icon: 'search',
				shortcut: 'G Q',
				category: 'Navigation',
				keywords: ['home', 'search', 'ask', 'question'],
				priority: 100,
				action: () => goto('/')
			},
			{
				id: 'nav-documents',
				label: 'Go to Documents',
				description: 'Manage your documents',
				icon: 'file-text',
				shortcut: 'G D',
				category: 'Navigation',
				keywords: ['files', 'upload', 'manage'],
				priority: 90,
				action: () => goto('/documents')
			},
			{
				id: 'nav-collections',
				label: 'Go to Collections',
				description: 'Organise your collections',
				icon: 'folder',
				shortcut: 'G C',
				category: 'Navigation',
				keywords: ['folders', 'groups', 'organise'],
				priority: 80,
				action: () => goto('/collections')
			},
			{
				id: 'nav-history',
				label: 'Go to History',
				description: 'View query history',
				icon: 'clock',
				shortcut: 'G H',
				category: 'Navigation',
				keywords: ['past', 'previous', 'queries'],
				priority: 70,
				action: () => goto('/history')
			},
			{
				id: 'nav-analytics',
				label: 'Go to Analytics',
				description: 'View system analytics',
				icon: 'bar-chart-2',
				shortcut: 'G A',
				category: 'Navigation',
				keywords: ['stats', 'metrics', 'performance', 'dashboard'],
				priority: 60,
				action: () => goto('/analytics')
			},
			{
				id: 'nav-settings',
				label: 'Go to Settings',
				description: 'Configure preferences',
				icon: 'settings',
				shortcut: 'G S',
				category: 'Navigation',
				keywords: ['preferences', 'options', 'configure', 'theme'],
				priority: 50,
				action: () => goto('/settings')
			}
		]);

		// Action commands
		this.registerAll([
			{
				id: 'action-upload',
				label: 'Upload Document',
				description: 'Upload a new document',
				icon: 'upload',
				shortcut: 'U',
				category: 'Actions',
				keywords: ['add', 'import', 'file', 'pdf'],
				priority: 100,
				action: () => goto('/documents?action=upload')
			},
			{
				id: 'action-new-collection',
				label: 'Create Collection',
				description: 'Create a new collection',
				icon: 'folder-plus',
				shortcut: 'N C',
				category: 'Actions',
				keywords: ['add', 'new', 'folder'],
				priority: 90,
				action: () => goto('/collections?action=create')
			},
			{
				id: 'action-new-query',
				label: 'New Query',
				description: 'Start a new search query',
				icon: 'search',
				shortcut: 'N Q',
				category: 'Query',
				keywords: ['search', 'ask', 'question'],
				priority: 100,
				action: () => goto('/')
			}
		]);

		// Settings commands
		this.registerAll([
			{
				id: 'settings-theme-light',
				label: 'Switch to Light Theme',
				description: 'Use light colour scheme',
				icon: 'sun',
				category: 'Settings',
				keywords: ['appearance', 'mode', 'bright'],
				action: () => {
					// Will be connected to theme store
					document.documentElement.setAttribute('data-theme', 'light');
					localStorage.setItem('ragged-theme', 'light');
				}
			},
			{
				id: 'settings-theme-dark',
				label: 'Switch to Dark Theme',
				description: 'Use dark colour scheme',
				icon: 'moon',
				category: 'Settings',
				keywords: ['appearance', 'mode', 'night'],
				action: () => {
					document.documentElement.setAttribute('data-theme', 'dark');
					localStorage.setItem('ragged-theme', 'dark');
				}
			},
			{
				id: 'settings-theme-high-contrast',
				label: 'Switch to High Contrast',
				description: 'Use high contrast for accessibility',
				icon: 'contrast',
				category: 'Settings',
				keywords: ['accessibility', 'a11y', 'wcag'],
				action: () => {
					document.documentElement.setAttribute('data-theme', 'high-contrast');
					localStorage.setItem('ragged-theme', 'high-contrast');
				}
			}
		]);

		// Help commands
		this.registerAll([
			{
				id: 'help-shortcuts',
				label: 'Keyboard Shortcuts',
				description: 'View all keyboard shortcuts',
				icon: 'keyboard',
				shortcut: '?',
				category: 'Help',
				keywords: ['keys', 'bindings', 'hotkeys'],
				action: () => {
					// Will open shortcuts modal
					console.log('Show shortcuts');
				}
			},
			{
				id: 'help-docs',
				label: 'Documentation',
				description: 'View documentation',
				icon: 'book-open',
				category: 'Help',
				keywords: ['guide', 'manual', 'help'],
				action: () => {
					window.open('https://github.com/ragged/ragged', '_blank');
				}
			}
		]);
	}
}

// Singleton instance
export const commandRegistry = new CommandRegistry();
