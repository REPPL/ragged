/**
 * Workflow Node Definitions
 * ragged WebUI v0.9.4
 *
 * Node type definitions for RAG pipeline components
 */

import type { NodeDefinition, NodeType } from './types';

export const NODE_DEFINITIONS: Record<NodeType, NodeDefinition> = {
	'document-input': {
		type: 'document-input',
		label: 'Document Input',
		description: 'Load documents from the library or upload new files',
		category: 'input',
		icon: 'file-text',
		colour: '#4f46e5',
		inputs: [],
		outputs: [{ name: 'documents', type: 'document' }],
		defaultConfig: {
			source: 'library',
			collectionId: '',
			maxDocuments: 10
		},
		configSchema: [
			{
				key: 'source',
				label: 'Source',
				type: 'select',
				options: [
					{ value: 'library', label: 'Document Library' },
					{ value: 'upload', label: 'File Upload' },
					{ value: 'url', label: 'URL Fetch' }
				],
				default: 'library'
			},
			{
				key: 'collectionId',
				label: 'Collection',
				type: 'text',
				placeholder: 'default'
			},
			{
				key: 'maxDocuments',
				label: 'Max Documents',
				type: 'number',
				default: 10
			}
		]
	},

	'text-input': {
		type: 'text-input',
		label: 'Text Input',
		description: 'Provide static text or template',
		category: 'input',
		icon: 'type',
		colour: '#4f46e5',
		inputs: [],
		outputs: [{ name: 'text', type: 'text' }],
		defaultConfig: {
			text: ''
		},
		configSchema: [
			{
				key: 'text',
				label: 'Text Content',
				type: 'textarea',
				placeholder: 'Enter text...'
			}
		]
	},

	'query-input': {
		type: 'query-input',
		label: 'Query Input',
		description: 'User query or question input',
		category: 'input',
		icon: 'search',
		colour: '#4f46e5',
		inputs: [],
		outputs: [{ name: 'query', type: 'query' }],
		defaultConfig: {
			mode: 'runtime',
			defaultQuery: ''
		},
		configSchema: [
			{
				key: 'mode',
				label: 'Mode',
				type: 'select',
				options: [
					{ value: 'runtime', label: 'Runtime Input' },
					{ value: 'static', label: 'Static Query' }
				],
				default: 'runtime'
			},
			{
				key: 'defaultQuery',
				label: 'Default Query',
				type: 'text',
				placeholder: 'Enter default query...'
			}
		]
	},

	embedding: {
		type: 'embedding',
		label: 'Embedding',
		description: 'Generate embeddings using local or API models',
		category: 'processing',
		icon: 'cpu',
		colour: '#059669',
		inputs: [{ name: 'input', type: 'any' }],
		outputs: [{ name: 'embeddings', type: 'embedding' }],
		defaultConfig: {
			model: 'all-MiniLM-L6-v2',
			batchSize: 32,
			normalise: true
		},
		configSchema: [
			{
				key: 'model',
				label: 'Model',
				type: 'select',
				options: [
					{ value: 'all-MiniLM-L6-v2', label: 'MiniLM L6 v2 (Fast)' },
					{ value: 'all-mpnet-base-v2', label: 'MPNet Base v2 (Balanced)' },
					{ value: 'bge-small-en-v1.5', label: 'BGE Small EN (Quality)' },
					{ value: 'custom', label: 'Custom Model' }
				],
				default: 'all-MiniLM-L6-v2'
			},
			{
				key: 'batchSize',
				label: 'Batch Size',
				type: 'number',
				default: 32
			},
			{
				key: 'normalise',
				label: 'Normalise Embeddings',
				type: 'boolean',
				default: true
			}
		]
	},

	retrieval: {
		type: 'retrieval',
		label: 'Retrieval',
		description: 'Retrieve relevant documents using vector similarity',
		category: 'retrieval',
		icon: 'database',
		colour: '#0891b2',
		inputs: [
			{ name: 'query', type: 'query' },
			{ name: 'embeddings', type: 'embedding' }
		],
		outputs: [{ name: 'results', type: 'document' }],
		defaultConfig: {
			topK: 5,
			threshold: 0.7,
			collection: 'default'
		},
		configSchema: [
			{
				key: 'topK',
				label: 'Top K Results',
				type: 'number',
				default: 5
			},
			{
				key: 'threshold',
				label: 'Similarity Threshold',
				type: 'number',
				default: 0.7
			},
			{
				key: 'collection',
				label: 'Collection',
				type: 'text',
				default: 'default'
			}
		]
	},

	reranker: {
		type: 'reranker',
		label: 'Reranker',
		description: 'Rerank retrieved documents for relevance',
		category: 'retrieval',
		icon: 'list-ordered',
		colour: '#0891b2',
		inputs: [
			{ name: 'query', type: 'query' },
			{ name: 'documents', type: 'document' }
		],
		outputs: [{ name: 'reranked', type: 'document' }],
		defaultConfig: {
			model: 'cross-encoder',
			topK: 3
		},
		configSchema: [
			{
				key: 'model',
				label: 'Reranker Model',
				type: 'select',
				options: [
					{ value: 'cross-encoder', label: 'Cross-Encoder' },
					{ value: 'cohere', label: 'Cohere Rerank' },
					{ value: 'custom', label: 'Custom Model' }
				],
				default: 'cross-encoder'
			},
			{
				key: 'topK',
				label: 'Top K Results',
				type: 'number',
				default: 3
			}
		]
	},

	llm: {
		type: 'llm',
		label: 'LLM',
		description: 'Generate response using language model',
		category: 'processing',
		icon: 'brain',
		colour: '#059669',
		inputs: [
			{ name: 'prompt', type: 'text' },
			{ name: 'context', type: 'document' }
		],
		outputs: [{ name: 'response', type: 'text' }],
		defaultConfig: {
			provider: 'ollama',
			model: 'llama3.2',
			temperature: 0.7,
			maxTokens: 1024
		},
		configSchema: [
			{
				key: 'provider',
				label: 'Provider',
				type: 'select',
				options: [
					{ value: 'ollama', label: 'Ollama (Local)' },
					{ value: 'openai', label: 'OpenAI' },
					{ value: 'anthropic', label: 'Anthropic' },
					{ value: 'custom', label: 'Custom Endpoint' }
				],
				default: 'ollama'
			},
			{
				key: 'model',
				label: 'Model',
				type: 'text',
				default: 'llama3.2'
			},
			{
				key: 'temperature',
				label: 'Temperature',
				type: 'number',
				default: 0.7
			},
			{
				key: 'maxTokens',
				label: 'Max Tokens',
				type: 'number',
				default: 1024
			}
		]
	},

	'prompt-template': {
		type: 'prompt-template',
		label: 'Prompt Template',
		description: 'Create structured prompts with variables',
		category: 'utility',
		icon: 'file-edit',
		colour: '#d97706',
		inputs: [
			{ name: 'context', type: 'any' },
			{ name: 'query', type: 'query' }
		],
		outputs: [{ name: 'prompt', type: 'text' }],
		defaultConfig: {
			template: `You are a helpful assistant. Answer the question based on the provided context.

Context:
{{context}}

Question: {{query}}

Answer:`
		},
		configSchema: [
			{
				key: 'template',
				label: 'Prompt Template',
				type: 'textarea',
				placeholder: 'Use {{variable}} for placeholders'
			}
		]
	},

	filter: {
		type: 'filter',
		label: 'Filter',
		description: 'Filter documents by metadata or content',
		category: 'utility',
		icon: 'filter',
		colour: '#d97706',
		inputs: [{ name: 'documents', type: 'document' }],
		outputs: [{ name: 'filtered', type: 'document' }],
		defaultConfig: {
			field: '',
			operator: 'equals',
			value: ''
		},
		configSchema: [
			{
				key: 'field',
				label: 'Field',
				type: 'text',
				placeholder: 'metadata.field'
			},
			{
				key: 'operator',
				label: 'Operator',
				type: 'select',
				options: [
					{ value: 'equals', label: 'Equals' },
					{ value: 'contains', label: 'Contains' },
					{ value: 'gt', label: 'Greater Than' },
					{ value: 'lt', label: 'Less Than' },
					{ value: 'exists', label: 'Exists' }
				],
				default: 'equals'
			},
			{
				key: 'value',
				label: 'Value',
				type: 'text'
			}
		]
	},

	merge: {
		type: 'merge',
		label: 'Merge',
		description: 'Combine multiple document streams',
		category: 'utility',
		icon: 'git-merge',
		colour: '#d97706',
		inputs: [
			{ name: 'input1', type: 'any' },
			{ name: 'input2', type: 'any' }
		],
		outputs: [{ name: 'merged', type: 'any' }],
		defaultConfig: {
			mode: 'concatenate',
			deduplicate: true
		},
		configSchema: [
			{
				key: 'mode',
				label: 'Merge Mode',
				type: 'select',
				options: [
					{ value: 'concatenate', label: 'Concatenate' },
					{ value: 'interleave', label: 'Interleave' },
					{ value: 'union', label: 'Union' }
				],
				default: 'concatenate'
			},
			{
				key: 'deduplicate',
				label: 'Remove Duplicates',
				type: 'boolean',
				default: true
			}
		]
	},

	split: {
		type: 'split',
		label: 'Split',
		description: 'Split documents into chunks',
		category: 'utility',
		icon: 'scissors',
		colour: '#d97706',
		inputs: [{ name: 'documents', type: 'document' }],
		outputs: [{ name: 'chunks', type: 'document' }],
		defaultConfig: {
			chunkSize: 512,
			chunkOverlap: 50,
			separator: '\n\n'
		},
		configSchema: [
			{
				key: 'chunkSize',
				label: 'Chunk Size',
				type: 'number',
				default: 512
			},
			{
				key: 'chunkOverlap',
				label: 'Chunk Overlap',
				type: 'number',
				default: 50
			},
			{
				key: 'separator',
				label: 'Separator',
				type: 'text',
				default: '\\n\\n'
			}
		]
	},

	output: {
		type: 'output',
		label: 'Output',
		description: 'Final output of the workflow',
		category: 'output',
		icon: 'log-out',
		colour: '#dc2626',
		inputs: [{ name: 'result', type: 'any' }],
		outputs: [],
		defaultConfig: {
			format: 'text',
			stream: false
		},
		configSchema: [
			{
				key: 'format',
				label: 'Output Format',
				type: 'select',
				options: [
					{ value: 'text', label: 'Plain Text' },
					{ value: 'markdown', label: 'Markdown' },
					{ value: 'json', label: 'JSON' }
				],
				default: 'text'
			},
			{
				key: 'stream',
				label: 'Stream Output',
				type: 'boolean',
				default: false
			}
		]
	},

	custom: {
		type: 'custom',
		label: 'Custom Node',
		description: 'Custom processing with user-defined logic',
		category: 'utility',
		icon: 'code',
		colour: '#6b7280',
		inputs: [{ name: 'input', type: 'any' }],
		outputs: [{ name: 'output', type: 'any' }],
		defaultConfig: {
			code: '// Process input and return output\nreturn input;'
		},
		configSchema: [
			{
				key: 'code',
				label: 'Processing Code',
				type: 'textarea',
				placeholder: '// JavaScript processing code'
			}
		]
	}
};

export function getNodesByCategory(): Record<string, NodeDefinition[]> {
	const categories: Record<string, NodeDefinition[]> = {
		input: [],
		processing: [],
		retrieval: [],
		output: [],
		utility: []
	};

	Object.values(NODE_DEFINITIONS).forEach((node) => {
		categories[node.category].push(node);
	});

	return categories;
}

export function createNode(
	type: NodeType,
	x: number,
	y: number,
	id?: string
): import('./types').WorkflowNode {
	const definition = NODE_DEFINITIONS[type];
	const nodeId = id || `${type}-${Date.now()}`;

	return {
		id: nodeId,
		type,
		label: definition.label,
		x,
		y,
		width: 180,
		height: 80 + Math.max(definition.inputs.length, definition.outputs.length) * 24,
		config: { ...definition.defaultConfig },
		inputs: definition.inputs.map((input, i) => ({
			id: `${nodeId}-input-${i}`,
			...input,
			connected: false
		})),
		outputs: definition.outputs.map((output, i) => ({
			id: `${nodeId}-output-${i}`,
			...output,
			connected: false
		}))
	};
}
