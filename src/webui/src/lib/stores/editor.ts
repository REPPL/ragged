/**
 * Editor store for block editor state management.
 *
 * v0.9.1: Initial implementation
 *
 * Manages:
 * - Document state (current document, unsaved changes)
 * - Document list
 * - Auto-save functionality
 * - Local storage persistence
 */

import { writable, derived, get } from 'svelte/store';

export interface EditorDocument {
	id: string;
	title: string;
	content: string;
	createdAt: Date;
	updatedAt: Date;
	tags?: string[];
}

interface EditorState {
	currentDocumentId: string | null;
	documents: Map<string, EditorDocument>;
	unsavedChanges: boolean;
	autoSaveEnabled: boolean;
	autoSaveInterval: number; // milliseconds
	loading: boolean;
	error: string | null;
}

const STORAGE_KEY = 'ragged-editor-documents';
const AUTO_SAVE_INTERVAL = 30000; // 30 seconds

function createEditorStore() {
	const initialState: EditorState = {
		currentDocumentId: null,
		documents: new Map(),
		unsavedChanges: false,
		autoSaveEnabled: true,
		autoSaveInterval: AUTO_SAVE_INTERVAL,
		loading: false,
		error: null
	};

	const { subscribe, set, update } = writable<EditorState>(initialState);

	// Load documents from local storage on initialisation
	function loadFromStorage(): void {
		if (typeof window === 'undefined') return;

		try {
			const stored = localStorage.getItem(STORAGE_KEY);
			if (stored) {
				const parsed = JSON.parse(stored);
				const documents = new Map<string, EditorDocument>();

				for (const doc of parsed.documents || []) {
					documents.set(doc.id, {
						...doc,
						createdAt: new Date(doc.createdAt),
						updatedAt: new Date(doc.updatedAt)
					});
				}

				update((state) => ({
					...state,
					documents,
					currentDocumentId: parsed.currentDocumentId || null
				}));
			}
		} catch (err) {
			console.error('Failed to load editor documents from storage:', err);
		}
	}

	// Save documents to local storage
	function saveToStorage(): void {
		if (typeof window === 'undefined') return;

		try {
			const state = get({ subscribe });
			const documents = Array.from(state.documents.values());

			localStorage.setItem(
				STORAGE_KEY,
				JSON.stringify({
					currentDocumentId: state.currentDocumentId,
					documents
				})
			);
		} catch (err) {
			console.error('Failed to save editor documents to storage:', err);
		}
	}

	return {
		subscribe,

		// Initialise the store
		init(): void {
			loadFromStorage();
		},

		// Create a new document
		createDocument(title: string = 'Untitled'): EditorDocument {
			const doc: EditorDocument = {
				id: crypto.randomUUID(),
				title,
				content: '',
				createdAt: new Date(),
				updatedAt: new Date()
			};

			update((state) => {
				state.documents.set(doc.id, doc);
				return {
					...state,
					currentDocumentId: doc.id,
					unsavedChanges: false
				};
			});

			saveToStorage();
			return doc;
		},

		// Load a document by ID
		async loadDocument(id: string): Promise<EditorDocument | null> {
			update((state) => ({ ...state, loading: true, error: null }));

			try {
				const state = get({ subscribe });
				const doc = state.documents.get(id);

				if (doc) {
					update((s) => ({
						...s,
						currentDocumentId: id,
						loading: false,
						unsavedChanges: false
					}));
					return doc;
				}

				// Document not found locally - could fetch from API here
				update((s) => ({
					...s,
					loading: false,
					error: 'Document not found'
				}));
				return null;
			} catch (err) {
				const message = err instanceof Error ? err.message : 'Failed to load document';
				update((s) => ({
					...s,
					loading: false,
					error: message
				}));
				return null;
			}
		},

		// Save a document
		async saveDocument(doc: EditorDocument): Promise<EditorDocument> {
			doc.updatedAt = new Date();

			update((state) => {
				state.documents.set(doc.id, doc);
				return {
					...state,
					currentDocumentId: doc.id,
					unsavedChanges: false
				};
			});

			saveToStorage();
			return doc;
		},

		// Update document content
		updateContent(id: string, content: string): void {
			update((state) => {
				const doc = state.documents.get(id);
				if (doc) {
					doc.content = content;
					doc.updatedAt = new Date();
					state.documents.set(id, doc);
				}
				return {
					...state,
					unsavedChanges: true
				};
			});
		},

		// Delete a document
		deleteDocument(id: string): void {
			update((state) => {
				state.documents.delete(id);
				return {
					...state,
					currentDocumentId: state.currentDocumentId === id ? null : state.currentDocumentId
				};
			});
			saveToStorage();
		},

		// Set unsaved changes flag
		setUnsavedChanges(hasChanges: boolean): void {
			update((state) => ({
				...state,
				unsavedChanges: hasChanges
			}));
		},

		// Get all documents as array
		getDocuments(): EditorDocument[] {
			const state = get({ subscribe });
			return Array.from(state.documents.values()).sort(
				(a, b) => b.updatedAt.getTime() - a.updatedAt.getTime()
			);
		},

		// Get current document
		getCurrentDocument(): EditorDocument | null {
			const state = get({ subscribe });
			if (!state.currentDocumentId) return null;
			return state.documents.get(state.currentDocumentId) || null;
		},

		// Clear all documents
		clearAll(): void {
			update((state) => ({
				...state,
				documents: new Map(),
				currentDocumentId: null,
				unsavedChanges: false
			}));
			localStorage.removeItem(STORAGE_KEY);
		},

		// Export document as markdown
		exportAsMarkdown(id: string): string | null {
			const state = get({ subscribe });
			const doc = state.documents.get(id);
			if (!doc) return null;

			// Basic HTML to Markdown conversion
			return doc.content
				.replace(/<h1[^>]*>(.*?)<\/h1>/gi, '# $1\n\n')
				.replace(/<h2[^>]*>(.*?)<\/h2>/gi, '## $1\n\n')
				.replace(/<h3[^>]*>(.*?)<\/h3>/gi, '### $1\n\n')
				.replace(/<p[^>]*>(.*?)<\/p>/gi, '$1\n\n')
				.replace(/<strong[^>]*>(.*?)<\/strong>/gi, '**$1**')
				.replace(/<em[^>]*>(.*?)<\/em>/gi, '_$1_')
				.replace(/<code[^>]*>(.*?)<\/code>/gi, '`$1`')
				.replace(/<br\s*\/?>/gi, '\n')
				.replace(/<hr\s*\/?>/gi, '\n---\n')
				.replace(/<[^>]+>/g, '')
				.trim();
		},

		// Toggle auto-save
		toggleAutoSave(): void {
			update((state) => ({
				...state,
				autoSaveEnabled: !state.autoSaveEnabled
			}));
		}
	};
}

export const editorStore = createEditorStore();

// Derived stores for convenience
export const currentDocument = derived(editorStore, ($store) =>
	$store.currentDocumentId ? $store.documents.get($store.currentDocumentId) || null : null
);

export const documentList = derived(editorStore, ($store) =>
	Array.from($store.documents.values()).sort(
		(a, b) => b.updatedAt.getTime() - a.updatedAt.getTime()
	)
);

export const hasUnsavedChanges = derived(editorStore, ($store) => $store.unsavedChanges);

export const isLoading = derived(editorStore, ($store) => $store.loading);

export const editorError = derived(editorStore, ($store) => $store.error);
