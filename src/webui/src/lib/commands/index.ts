/**
 * Commands Module
 * ragged WebUI v0.9.1
 *
 * Barrel export for command palette infrastructure
 */

export { commandRegistry, type Command, type CommandCategory } from './registry';
export {
	createCommandSearch,
	searchCommands,
	highlightMatches,
	getMatchIndices,
	type SearchResult,
	type SearchOptions
} from './search';
