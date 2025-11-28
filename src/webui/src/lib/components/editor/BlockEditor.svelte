<script lang="ts">
	/**
	 * BlockEditor - TipTap-based block editor for ragged.
	 *
	 * v0.9.1: Initial MVP implementation
	 *
	 * Features:
	 * - Rich text editing with TipTap
	 * - Custom blocks (query, document, citation)
	 * - Drag-and-drop reordering
	 * - Slash commands
	 * - Export to markdown
	 */

	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { Editor } from '@tiptap/core';
	import StarterKit from '@tiptap/starter-kit';
	import Placeholder from '@tiptap/extension-placeholder';
	import Image from '@tiptap/extension-image';
	import Table from '@tiptap/extension-table';
	import TableRow from '@tiptap/extension-table-row';
	import TableCell from '@tiptap/extension-table-cell';
	import TableHeader from '@tiptap/extension-table-header';
	import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight';
	import { common, createLowlight } from 'lowlight';

	import { QueryBlockExtension } from '$lib/editor/extensions/QueryBlock';
	import { DocumentBlockExtension } from '$lib/editor/extensions/DocumentBlock';
	import { CitationBlockExtension } from '$lib/editor/extensions/CitationBlock';
	import { editorStore, type EditorDocument } from '$lib/stores/editor';

	export let documentId: string | null = null;
	export let initialContent: string = '';
	export let placeholder: string = 'Start typing or use / for commands...';
	export let editable: boolean = true;

	const dispatch = createEventDispatcher<{
		save: { content: string; html: string };
		change: { content: string };
		queryExecuted: { query: string; results: unknown[] };
	}>();

	let element: HTMLElement;
	let editor: Editor | null = null;
	let showSlashMenu = false;
	let slashMenuPosition = { x: 0, y: 0 };
	let slashMenuQuery = '';

	const lowlight = createLowlight(common);

	const slashCommands = [
		{ name: 'Query', description: 'Execute a RAG query', icon: 'search', command: 'query' },
		{ name: 'Document', description: 'Reference a document', icon: 'file', command: 'document' },
		{ name: 'Citation', description: 'Insert a citation', icon: 'quote', command: 'citation' },
		{ name: 'Heading 1', description: 'Large heading', icon: 'h1', command: 'h1' },
		{ name: 'Heading 2', description: 'Medium heading', icon: 'h2', command: 'h2' },
		{ name: 'Heading 3', description: 'Small heading', icon: 'h3', command: 'h3' },
		{ name: 'Code Block', description: 'Syntax-highlighted code', icon: 'code', command: 'code' },
		{ name: 'Image', description: 'Insert an image', icon: 'image', command: 'image' },
		{ name: 'Table', description: 'Insert a table', icon: 'table', command: 'table' },
		{ name: 'Horizontal Rule', description: 'Divider line', icon: 'minus', command: 'hr' }
	];

	$: filteredCommands = slashCommands.filter(
		(cmd) =>
			cmd.name.toLowerCase().includes(slashMenuQuery.toLowerCase()) ||
			cmd.description.toLowerCase().includes(slashMenuQuery.toLowerCase())
	);

	onMount(() => {
		editor = new Editor({
			element,
			extensions: [
				StarterKit.configure({
					codeBlock: false
				}),
				Placeholder.configure({
					placeholder
				}),
				Image.configure({
					allowBase64: true,
					inline: false
				}),
				Table.configure({
					resizable: true
				}),
				TableRow,
				TableCell,
				TableHeader,
				CodeBlockLowlight.configure({
					lowlight
				}),
				QueryBlockExtension,
				DocumentBlockExtension,
				CitationBlockExtension
			],
			content: initialContent,
			editable,
			onUpdate: ({ editor: e }) => {
				dispatch('change', { content: e.getHTML() });
				editorStore.setUnsavedChanges(true);
			},
			onTransaction: ({ editor: e, transaction }) => {
				// Check for slash command trigger
				if (transaction.docChanged) {
					const { $from } = e.state.selection;
					const textBefore = $from.nodeBefore?.textContent || '';
					const lastSlash = textBefore.lastIndexOf('/');

					if (lastSlash !== -1 && lastSlash === textBefore.length - 1) {
						// Show slash menu
						const coords = e.view.coordsAtPos($from.pos);
						slashMenuPosition = { x: coords.left, y: coords.bottom + 8 };
						showSlashMenu = true;
						slashMenuQuery = '';
					} else if (showSlashMenu && textBefore.includes('/')) {
						// Update query
						slashMenuQuery = textBefore.substring(textBefore.lastIndexOf('/') + 1);
					} else {
						showSlashMenu = false;
					}
				}
			}
		});

		// Load document if ID provided
		if (documentId) {
			loadDocument(documentId);
		}

		return () => {
			if (editor) {
				editor.destroy();
			}
		};
	});

	onDestroy(() => {
		if (editor) {
			editor.destroy();
		}
	});

	async function loadDocument(id: string) {
		try {
			const doc = await editorStore.loadDocument(id);
			if (doc && editor) {
				editor.commands.setContent(doc.content);
			}
		} catch (err) {
			console.error('Failed to load document:', err);
		}
	}

	function executeSlashCommand(command: string) {
		if (!editor) return;

		// Remove the slash and query from the editor
		const { $from } = editor.state.selection;
		const textBefore = $from.nodeBefore?.textContent || '';
		const slashPos = textBefore.lastIndexOf('/');
		if (slashPos !== -1) {
			editor.commands.deleteRange({
				from: $from.pos - (textBefore.length - slashPos),
				to: $from.pos
			});
		}

		showSlashMenu = false;

		switch (command) {
			case 'query':
				editor.commands.insertContent({
					type: 'queryBlock',
					attrs: { query: '', results: [] }
				});
				break;
			case 'document':
				editor.commands.insertContent({
					type: 'documentBlock',
					attrs: { documentId: '', title: 'Select document...' }
				});
				break;
			case 'citation':
				editor.commands.insertContent({
					type: 'citationBlock',
					attrs: { source: '', text: '' }
				});
				break;
			case 'h1':
				editor.chain().focus().toggleHeading({ level: 1 }).run();
				break;
			case 'h2':
				editor.chain().focus().toggleHeading({ level: 2 }).run();
				break;
			case 'h3':
				editor.chain().focus().toggleHeading({ level: 3 }).run();
				break;
			case 'code':
				editor.chain().focus().toggleCodeBlock().run();
				break;
			case 'image':
				const url = prompt('Enter image URL:');
				if (url) {
					editor.chain().focus().setImage({ src: url }).run();
				}
				break;
			case 'table':
				editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run();
				break;
			case 'hr':
				editor.chain().focus().setHorizontalRule().run();
				break;
		}
	}

	export function getContent(): string {
		return editor?.getHTML() || '';
	}

	export function getMarkdown(): string {
		// Basic HTML to Markdown conversion
		const html = editor?.getHTML() || '';
		return html
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
	}

	export async function save(): Promise<EditorDocument | null> {
		if (!editor) return null;

		const content = editor.getHTML();
		const doc = await editorStore.saveDocument({
			id: documentId || crypto.randomUUID(),
			title: extractTitle(content),
			content,
			createdAt: new Date(),
			updatedAt: new Date()
		});

		dispatch('save', { content, html: content });
		return doc;
	}

	function extractTitle(html: string): string {
		const match = html.match(/<h[1-3][^>]*>(.*?)<\/h[1-3]>/i);
		if (match) {
			return match[1].replace(/<[^>]+>/g, '').trim();
		}
		// Fall back to first line of text
		const text = html.replace(/<[^>]+>/g, '').trim();
		return text.substring(0, 50) || 'Untitled';
	}

	function handleKeydown(event: KeyboardEvent) {
		if (showSlashMenu) {
			if (event.key === 'Escape') {
				showSlashMenu = false;
				event.preventDefault();
			} else if (event.key === 'Enter' && filteredCommands.length > 0) {
				executeSlashCommand(filteredCommands[0].command);
				event.preventDefault();
			} else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
				// TODO: Navigate menu items
				event.preventDefault();
			}
		}

		// Save shortcut
		if ((event.metaKey || event.ctrlKey) && event.key === 's') {
			event.preventDefault();
			save();
		}
	}
</script>

<div class="block-editor" on:keydown={handleKeydown}>
	<!-- Toolbar -->
	<div class="editor-toolbar">
		<div class="toolbar-group">
			<button
				class="toolbar-btn"
				class:active={editor?.isActive('bold')}
				on:click={() => editor?.chain().focus().toggleBold().run()}
				title="Bold (Ctrl+B)"
			>
				<span class="icon">B</span>
			</button>
			<button
				class="toolbar-btn"
				class:active={editor?.isActive('italic')}
				on:click={() => editor?.chain().focus().toggleItalic().run()}
				title="Italic (Ctrl+I)"
			>
				<span class="icon italic">I</span>
			</button>
			<button
				class="toolbar-btn"
				class:active={editor?.isActive('strike')}
				on:click={() => editor?.chain().focus().toggleStrike().run()}
				title="Strikethrough"
			>
				<span class="icon strike">S</span>
			</button>
		</div>

		<div class="toolbar-separator"></div>

		<div class="toolbar-group">
			<button
				class="toolbar-btn"
				class:active={editor?.isActive('heading', { level: 1 })}
				on:click={() => editor?.chain().focus().toggleHeading({ level: 1 }).run()}
				title="Heading 1"
			>
				H1
			</button>
			<button
				class="toolbar-btn"
				class:active={editor?.isActive('heading', { level: 2 })}
				on:click={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()}
				title="Heading 2"
			>
				H2
			</button>
			<button
				class="toolbar-btn"
				class:active={editor?.isActive('heading', { level: 3 })}
				on:click={() => editor?.chain().focus().toggleHeading({ level: 3 }).run()}
				title="Heading 3"
			>
				H3
			</button>
		</div>

		<div class="toolbar-separator"></div>

		<div class="toolbar-group">
			<button
				class="toolbar-btn"
				class:active={editor?.isActive('bulletList')}
				on:click={() => editor?.chain().focus().toggleBulletList().run()}
				title="Bullet List"
			>
				<span class="icon">&#8226;</span>
			</button>
			<button
				class="toolbar-btn"
				class:active={editor?.isActive('orderedList')}
				on:click={() => editor?.chain().focus().toggleOrderedList().run()}
				title="Numbered List"
			>
				<span class="icon">1.</span>
			</button>
			<button
				class="toolbar-btn"
				class:active={editor?.isActive('blockquote')}
				on:click={() => editor?.chain().focus().toggleBlockquote().run()}
				title="Quote"
			>
				<span class="icon">"</span>
			</button>
		</div>

		<div class="toolbar-separator"></div>

		<div class="toolbar-group">
			<button
				class="toolbar-btn"
				class:active={editor?.isActive('codeBlock')}
				on:click={() => editor?.chain().focus().toggleCodeBlock().run()}
				title="Code Block"
			>
				<span class="icon">&lt;/&gt;</span>
			</button>
			<button
				class="toolbar-btn"
				on:click={() => editor?.chain().focus().setHorizontalRule().run()}
				title="Horizontal Rule"
			>
				<span class="icon">&#8212;</span>
			</button>
		</div>

		<div class="toolbar-spacer"></div>

		<div class="toolbar-group">
			<button class="toolbar-btn save-btn" on:click={save} title="Save (Ctrl+S)"> Save </button>
		</div>
	</div>

	<!-- Editor Content -->
	<div class="editor-content" bind:this={element}></div>

	<!-- Slash Command Menu -->
	{#if showSlashMenu}
		<div
			class="slash-menu"
			style="left: {slashMenuPosition.x}px; top: {slashMenuPosition.y}px;"
		>
			{#each filteredCommands as cmd}
				<button class="slash-menu-item" on:click={() => executeSlashCommand(cmd.command)}>
					<span class="slash-menu-icon">{cmd.icon}</span>
					<div class="slash-menu-content">
						<span class="slash-menu-name">{cmd.name}</span>
						<span class="slash-menu-desc">{cmd.description}</span>
					</div>
				</button>
			{/each}
			{#if filteredCommands.length === 0}
				<div class="slash-menu-empty">No commands found</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.block-editor {
		display: flex;
		flex-direction: column;
		height: 100%;
		background: var(--color-background);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		overflow: hidden;
	}

	.editor-toolbar {
		display: flex;
		align-items: center;
		padding: var(--space-2) var(--space-3);
		background: var(--color-surface);
		border-bottom: 1px solid var(--color-border);
		gap: var(--space-1);
		flex-wrap: wrap;
	}

	.toolbar-group {
		display: flex;
		gap: var(--space-1);
	}

	.toolbar-separator {
		width: 1px;
		height: 24px;
		background: var(--color-border);
		margin: 0 var(--space-2);
	}

	.toolbar-spacer {
		flex: 1;
	}

	.toolbar-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 32px;
		height: 32px;
		padding: 0 var(--space-2);
		border: none;
		border-radius: var(--radius-sm);
		background: transparent;
		color: var(--color-text-secondary);
		cursor: pointer;
		font-size: 14px;
		font-weight: 500;
		transition: all 0.15s ease;
	}

	.toolbar-btn:hover {
		background: var(--color-background-hover);
		color: var(--color-text);
	}

	.toolbar-btn.active {
		background: var(--color-primary-light);
		color: var(--color-primary);
	}

	.toolbar-btn .icon {
		font-family: serif;
		font-size: 16px;
	}

	.toolbar-btn .icon.italic {
		font-style: italic;
	}

	.toolbar-btn .icon.strike {
		text-decoration: line-through;
	}

	.save-btn {
		background: var(--color-primary);
		color: white;
		padding: 0 var(--space-3);
	}

	.save-btn:hover {
		background: var(--color-primary-dark);
		color: white;
	}

	.editor-content {
		flex: 1;
		padding: var(--space-4);
		overflow-y: auto;
	}

	.editor-content :global(.ProseMirror) {
		min-height: 300px;
		outline: none;
	}

	.editor-content :global(.ProseMirror p.is-editor-empty:first-child::before) {
		content: attr(data-placeholder);
		float: left;
		color: var(--color-text-muted);
		pointer-events: none;
		height: 0;
	}

	.editor-content :global(h1) {
		font-size: 2rem;
		font-weight: 700;
		margin: 1rem 0 0.5rem;
	}

	.editor-content :global(h2) {
		font-size: 1.5rem;
		font-weight: 600;
		margin: 0.75rem 0 0.5rem;
	}

	.editor-content :global(h3) {
		font-size: 1.25rem;
		font-weight: 600;
		margin: 0.5rem 0 0.25rem;
	}

	.editor-content :global(p) {
		margin: 0.5rem 0;
		line-height: 1.6;
	}

	.editor-content :global(blockquote) {
		border-left: 3px solid var(--color-primary);
		padding-left: var(--space-3);
		margin: var(--space-3) 0;
		color: var(--color-text-secondary);
		font-style: italic;
	}

	.editor-content :global(pre) {
		background: var(--color-code-background);
		border-radius: var(--radius-md);
		padding: var(--space-3);
		overflow-x: auto;
		font-family: var(--font-mono);
		font-size: 0.875rem;
	}

	.editor-content :global(code) {
		background: var(--color-code-background);
		padding: 0.125rem 0.375rem;
		border-radius: var(--radius-sm);
		font-family: var(--font-mono);
		font-size: 0.875em;
	}

	.editor-content :global(pre code) {
		background: none;
		padding: 0;
	}

	.editor-content :global(ul),
	.editor-content :global(ol) {
		padding-left: var(--space-4);
		margin: var(--space-2) 0;
	}

	.editor-content :global(li) {
		margin: var(--space-1) 0;
	}

	.editor-content :global(hr) {
		border: none;
		border-top: 1px solid var(--color-border);
		margin: var(--space-4) 0;
	}

	.editor-content :global(table) {
		border-collapse: collapse;
		margin: var(--space-3) 0;
		width: 100%;
	}

	.editor-content :global(th),
	.editor-content :global(td) {
		border: 1px solid var(--color-border);
		padding: var(--space-2);
		text-align: left;
	}

	.editor-content :global(th) {
		background: var(--color-surface);
		font-weight: 600;
	}

	.editor-content :global(img) {
		max-width: 100%;
		height: auto;
		border-radius: var(--radius-md);
		margin: var(--space-3) 0;
	}

	/* Slash Menu */
	.slash-menu {
		position: fixed;
		z-index: 1000;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-lg);
		min-width: 240px;
		max-height: 320px;
		overflow-y: auto;
		padding: var(--space-1);
	}

	.slash-menu-item {
		display: flex;
		align-items: center;
		width: 100%;
		padding: var(--space-2);
		border: none;
		border-radius: var(--radius-sm);
		background: transparent;
		cursor: pointer;
		text-align: left;
		gap: var(--space-2);
	}

	.slash-menu-item:hover {
		background: var(--color-background-hover);
	}

	.slash-menu-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		background: var(--color-background);
		border-radius: var(--radius-sm);
		font-size: 14px;
		color: var(--color-text-secondary);
	}

	.slash-menu-content {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.slash-menu-name {
		font-weight: 500;
		color: var(--color-text);
	}

	.slash-menu-desc {
		font-size: 12px;
		color: var(--color-text-secondary);
	}

	.slash-menu-empty {
		padding: var(--space-3);
		text-align: center;
		color: var(--color-text-muted);
		font-size: 14px;
	}
</style>
