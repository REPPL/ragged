/**
 * DocumentBlock - TipTap extension for document references.
 *
 * v0.9.1: Initial implementation
 *
 * Allows users to embed references to ingested documents
 * with preview and metadata.
 */

import { Node, mergeAttributes } from '@tiptap/core';

export interface DocumentBlockAttributes {
	documentId: string;
	title: string;
	filename: string;
	excerpt: string;
	metadata: Record<string, unknown>;
}

declare module '@tiptap/core' {
	interface Commands<ReturnType> {
		documentBlock: {
			setDocumentBlock: (attributes?: Partial<DocumentBlockAttributes>) => ReturnType;
		};
	}
}

export const DocumentBlockExtension = Node.create({
	name: 'documentBlock',

	group: 'block',

	atom: true,

	addAttributes() {
		return {
			documentId: {
				default: ''
			},
			title: {
				default: 'Untitled Document'
			},
			filename: {
				default: ''
			},
			excerpt: {
				default: ''
			},
			metadata: {
				default: {}
			}
		};
	},

	parseHTML() {
		return [
			{
				tag: 'div[data-type="document-block"]'
			}
		];
	},

	renderHTML({ HTMLAttributes }) {
		return [
			'div',
			mergeAttributes(HTMLAttributes, {
				'data-type': 'document-block',
				class: 'document-block'
			}),
			[
				'div',
				{ class: 'document-block-icon' },
				['span', {}, '\uD83D\uDCC4'] // Document emoji
			],
			[
				'div',
				{ class: 'document-block-content' },
				['div', { class: 'document-block-title' }, HTMLAttributes.title || 'Select document...'],
				['div', { class: 'document-block-filename' }, HTMLAttributes.filename || ''],
				HTMLAttributes.excerpt
					? ['div', { class: 'document-block-excerpt' }, HTMLAttributes.excerpt]
					: ''
			]
		];
	},

	addCommands() {
		return {
			setDocumentBlock:
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

export default DocumentBlockExtension;
