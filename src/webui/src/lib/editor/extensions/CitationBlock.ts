/**
 * CitationBlock - TipTap extension for citations.
 *
 * v0.9.1: Initial implementation
 *
 * Allows users to insert citations from query results
 * with automatic formatting and source links.
 */

import { Node, mergeAttributes } from '@tiptap/core';

export interface CitationBlockAttributes {
	source: string;
	text: string;
	documentId: string;
	chunkId: string;
	score: number;
}

declare module '@tiptap/core' {
	interface Commands<ReturnType> {
		citationBlock: {
			setCitationBlock: (attributes?: Partial<CitationBlockAttributes>) => ReturnType;
		};
	}
}

export const CitationBlockExtension = Node.create({
	name: 'citationBlock',

	group: 'block',

	atom: true,

	addAttributes() {
		return {
			source: {
				default: ''
			},
			text: {
				default: ''
			},
			documentId: {
				default: ''
			},
			chunkId: {
				default: ''
			},
			score: {
				default: 0
			}
		};
	},

	parseHTML() {
		return [
			{
				tag: 'div[data-type="citation-block"]'
			}
		];
	},

	renderHTML({ HTMLAttributes }) {
		return [
			'div',
			mergeAttributes(HTMLAttributes, {
				'data-type': 'citation-block',
				class: 'citation-block'
			}),
			[
				'div',
				{ class: 'citation-block-quote' },
				['span', { class: 'citation-mark' }, '\u201C'],
				HTMLAttributes.text || 'Citation text...',
				['span', { class: 'citation-mark' }, '\u201D']
			],
			[
				'div',
				{ class: 'citation-block-source' },
				['span', { class: 'citation-dash' }, '\u2014 '],
				HTMLAttributes.source || 'Source'
			]
		];
	},

	addCommands() {
		return {
			setCitationBlock:
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

export default CitationBlockExtension;
