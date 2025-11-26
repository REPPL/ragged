<!--
  Query Input Component
  ragged WebUI v0.7.3

  Main query textarea (1500x100px from design)
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import Button from '../Button.svelte';

	export let value = '';
	export let disabled = false;
	export let loading = false;
	export let placeholder = 'Ask anything about your documents...';

	const dispatch = createEventDispatcher<{
		submit: { query: string };
	}>();

	function handleKeydown(event: KeyboardEvent) {
		if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
			event.preventDefault();
			submit();
		}
	}

	function submit() {
		if (value.trim() && !disabled && !loading) {
			dispatch('submit', { query: value.trim() });
		}
	}

	function clear() {
		value = '';
	}

	$: canSubmit = value.trim().length > 0 && !disabled && !loading;
</script>

<div class="query-input">
	<div class="query-input__container">
		<textarea
			bind:value
			on:keydown={handleKeydown}
			disabled={disabled || loading}
			{placeholder}
			rows="4"
			class="query-input__textarea"
			aria-label="Query input"
		/>

		{#if value.length > 0}
			<button
				type="button"
				class="query-input__clear"
				on:click={clear}
				aria-label="Clear query"
				disabled={loading}
			>
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<circle cx="12" cy="12" r="10" />
					<path d="M15 9l-6 6M9 9l6 6" />
				</svg>
			</button>
		{/if}
	</div>

	<div class="query-input__footer">
		<div class="query-input__hints">
			<span class="query-input__hint">
				Press <kbd>⌘</kbd><kbd>Enter</kbd> to search
			</span>
			<span class="query-input__count">
				{value.length} characters
			</span>
		</div>

		<Button
			variant="primary"
			size="md"
			{loading}
			disabled={!canSubmit}
			on:click={submit}
		>
			{#if loading}
				Searching...
			{:else}
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<circle cx="11" cy="11" r="8" />
					<path d="M21 21l-4.35-4.35" />
				</svg>
				Search
			{/if}
		</Button>
	</div>
</div>

<style>
	.query-input {
		width: 100%;
		max-width: var(--query-input-max-width);
	}

	.query-input__container {
		position: relative;
	}

	.query-input__textarea {
		width: 100%;
		height: var(--query-input-height);
		padding: var(--space-4);
		padding-right: 40px;
		font-family: var(--font-sans);
		font-size: var(--font-size-base);
		line-height: var(--line-height-normal);
		color: var(--color-text-primary);
		background-color: var(--color-bg);
		border: 2px solid var(--color-border-medium);
		border-radius: var(--radius-lg);
		resize: none;
		transition:
			border-color var(--transition-fast),
			box-shadow var(--transition-fast);
	}

	.query-input__textarea::placeholder {
		color: var(--color-text-muted);
	}

	.query-input__textarea:hover:not(:disabled) {
		border-color: var(--color-border-dark);
	}

	.query-input__textarea:focus {
		outline: none;
		border-color: var(--color-primary);
		box-shadow: var(--shadow-focus);
	}

	.query-input__textarea:disabled {
		background-color: var(--color-bg-secondary);
		cursor: not-allowed;
	}

	.query-input__clear {
		position: absolute;
		top: var(--space-3);
		right: var(--space-3);
		display: flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		padding: 0;
		color: var(--color-text-muted);
		background: none;
		border: none;
		border-radius: var(--radius-full);
		cursor: pointer;
		transition: color var(--transition-fast), background-color var(--transition-fast);
	}

	.query-input__clear:hover:not(:disabled) {
		color: var(--color-text-primary);
		background-color: var(--color-bg-secondary);
	}

	.query-input__clear:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.query-input__footer {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-top: var(--space-3);
	}

	.query-input__hints {
		display: flex;
		align-items: center;
		gap: var(--space-4);
	}

	.query-input__hint {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.query-input__count {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
		font-variant-numeric: tabular-nums;
	}

	kbd {
		display: inline-block;
		padding: 2px 6px;
		font-family: var(--font-mono);
		font-size: var(--font-size-xs);
		background-color: var(--color-bg-tertiary);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-sm);
	}

	@media (max-width: 640px) {
		.query-input__hints {
			flex-direction: column;
			align-items: flex-start;
			gap: var(--space-1);
		}
	}
</style>
