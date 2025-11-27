/**
 * Command Search Utilities
 * ragged WebUI v0.9.1
 *
 * Fuzzy search for command palette using Fuse.js
 */

import Fuse from 'fuse.js';
import type { Command } from './registry';

export interface SearchResult {
	item: Command;
	score: number;
	matches?: ReadonlyArray<{
		key?: string;
		value?: string;
		indices: ReadonlyArray<readonly [number, number]>;
	}>;
}

export interface SearchOptions {
	/** Maximum number of results to return */
	limit?: number;
	/** Minimum score threshold (0-1, lower is better match) */
	threshold?: number;
}

const DEFAULT_OPTIONS: SearchOptions = {
	limit: 20,
	threshold: 0.4
};

/**
 * Create a Fuse instance for searching commands
 */
export function createCommandSearch(commands: Command[]): Fuse<Command> {
	return new Fuse(commands, {
		keys: [
			{ name: 'label', weight: 0.4 },
			{ name: 'description', weight: 0.25 },
			{ name: 'keywords', weight: 0.25 },
			{ name: 'category', weight: 0.1 }
		],
		threshold: 0.4,
		includeScore: true,
		includeMatches: true,
		ignoreLocation: true,
		minMatchCharLength: 1,
		shouldSort: true,
		findAllMatches: true
	});
}

/**
 * Search commands with fuzzy matching
 */
export function searchCommands(
	fuse: Fuse<Command>,
	query: string,
	options: SearchOptions = DEFAULT_OPTIONS
): SearchResult[] {
	if (!query.trim()) {
		return [];
	}

	const results = fuse.search(query, {
		limit: options.limit ?? DEFAULT_OPTIONS.limit
	});

	// Filter by threshold if specified
	const threshold = options.threshold ?? DEFAULT_OPTIONS.threshold;
	return results
		.filter((result) => (result.score ?? 0) <= threshold!)
		.map((result) => ({
			item: result.item,
			score: result.score ?? 0,
			matches: result.matches
		}));
}

/**
 * Highlight matched characters in a string
 */
export function highlightMatches(
	text: string,
	matches?: ReadonlyArray<readonly [number, number]>
): { text: string; highlight: boolean }[] {
	if (!matches || matches.length === 0) {
		return [{ text, highlight: false }];
	}

	const result: { text: string; highlight: boolean }[] = [];
	let lastIndex = 0;

	// Sort matches by start index
	const sortedMatches = [...matches].sort((a, b) => a[0] - b[0]);

	for (const [start, end] of sortedMatches) {
		// Add non-highlighted text before the match
		if (start > lastIndex) {
			result.push({ text: text.slice(lastIndex, start), highlight: false });
		}

		// Add highlighted text
		result.push({ text: text.slice(start, end + 1), highlight: true });
		lastIndex = end + 1;
	}

	// Add remaining text
	if (lastIndex < text.length) {
		result.push({ text: text.slice(lastIndex), highlight: false });
	}

	return result;
}

/**
 * Get match indices for a specific key from search results
 */
export function getMatchIndices(
	matches: ReadonlyArray<{
		key?: string;
		value?: string;
		indices: ReadonlyArray<readonly [number, number]>;
	}> | undefined,
	key: string
): ReadonlyArray<readonly [number, number]> | undefined {
	if (!matches) return undefined;
	const match = matches.find((m) => m.key === key);
	return match?.indices;
}
