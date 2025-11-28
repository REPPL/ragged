/**
 * QueryBlock - TipTap extension for inline RAG queries.
 *
 * v0.9.1: Initial implementation
 *
 * Allows users to embed RAG queries directly in the editor
 * with results displayed inline.
 */

import { Node, mergeAttributes } from '@tiptap/core';
import { SvelteNodeViewRenderer } from 'svelte-tiptap';

export interface QueryBlockAttributes {
	query: string;
	results: Array<{
		id: string;
		title: string;
		excerpt: string;
		score: number;
	}>;
	loading: boolean;
	error: string | null;
}

declare module '@tiptap/core' {
	interface Commands<ReturnType> {
		queryBlock: {
			setQueryBlock: (attributes?: Partial<QueryBlockAttributes>) => ReturnType;
		};
	}
}

export const QueryBlockExtension = Node.create({
	name: 'queryBlock',

	group: 'block',

	atom: true,

	addAttributes() {
		return {
			query: {
				default: ''
			},
			results: {
				default: []
			},
			loading: {
				default: false
			},
			error: {
				default: null
			}
		};
	},

	parseHTML() {
		return [
			{
				tag: 'div[data-type="query-block"]'
			}
		];
	},

	renderHTML({ HTMLAttributes }) {
		return [
			'div',
			mergeAttributes(HTMLAttributes, {
				'data-type': 'query-block',
				class: 'query-block'
			}),
			[
				'div',
				{ class: 'query-block-header' },
				[
					'input',
					{
						type: 'text',
						class: 'query-input',
						placeholder: 'Enter your query...',
						value: HTMLAttributes.query || ''
					}
				],
				['button', { class: 'query-execute-btn' }, 'Search']
			],
			['div', { class: 'query-results' }, 'Results will appear here...']
		];
	},

	addCommands() {
		return {
			setQueryBlock:
				(attributes) =>
				({ commands }) => {
					return commands.insertContent({
						type: this.name,
						attrs: attributes
					});
				}
		};
	}
});

export default QueryBlockExtension;
