<!--
  TextArea Component
  ragged WebUI v0.7.3

  Usage:
  <TextArea bind:value={content} rows={4} maxLength={1000} showCount />
-->
<script lang="ts">
	import type { HTMLTextareaAttributes } from 'svelte/elements';

	interface $$Props extends HTMLTextareaAttributes {
		value?: string;
		label?: string;
		error?: string;
		hint?: string;
		maxLength?: number;
		showCount?: boolean;
		autoResize?: boolean;
	}

	export let value = '';
	export let label: string | undefined = undefined;
	export let error: string | undefined = undefined;
	export let hint: string | undefined = undefined;
	export let maxLength: number | undefined = undefined;
	export let showCount = false;
	export let autoResize = false;

	const id = $$restProps.id || `textarea-${Math.random().toString(36).slice(2, 9)}`;

	$: hasError = !!error;
	$: charCount = value?.length || 0;

	function handleInput(event: Event) {
		const target = event.target as HTMLTextAreaElement;

		if (autoResize) {
			target.style.height = 'auto';
			target.style.height = `${target.scrollHeight}px`;
		}
	}
</script>

<div class="textarea-wrapper">
	{#if label}
		<label for={id} class="textarea__label">
			{label}
			{#if $$restProps.required}
				<span class="textarea__required" aria-hidden="true">*</span>
			{/if}
		</label>
	{/if}

	<textarea
		{id}
		bind:value
		class="textarea"
		class:textarea--error={hasError}
		class:textarea--auto-resize={autoResize}
		maxlength={maxLength}
		aria-invalid={hasError}
		aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
		on:input={handleInput}
		on:input
		on:change
		on:focus
		on:blur
		on:keydown
		{...$$restProps}
	/>

	<div class="textarea__footer">
		{#if error}
			<p id="{id}-error" class="textarea__error" role="alert">
				{error}
			</p>
		{:else if hint}
			<p id="{id}-hint" class="textarea__hint">
				{hint}
			</p>
		{:else}
			<span />
		{/if}

		{#if showCount}
			<span class="textarea__count" class:textarea__count--limit={maxLength && charCount >= maxLength}>
				{charCount}{maxLength ? `/${maxLength}` : ''}
			</span>
		{/if}
	</div>
</div>

<style>
	.textarea-wrapper {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
		width: 100%;
	}

	.textarea__label {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-primary);
	}

	.textarea__required {
		color: var(--color-danger);
		margin-left: var(--space-1);
	}

	.textarea {
		width: 100%;
		min-height: 100px;
		padding: var(--space-3);
		font-family: var(--font-sans);
		font-size: var(--font-size-base);
		line-height: var(--line-height-normal);
		color: var(--color-text-primary);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-medium);
		border-radius: var(--radius-md);
		resize: vertical;
		transition:
			border-color var(--transition-fast),
			box-shadow var(--transition-fast);
	}

	.textarea::placeholder {
		color: var(--color-text-muted);
	}

	.textarea:hover:not(:disabled) {
		border-color: var(--color-border-dark);
	}

	.textarea:focus {
		outline: none;
		border-color: var(--color-primary);
		box-shadow: var(--shadow-focus);
	}

	.textarea:disabled {
		background-color: var(--color-bg-secondary);
		color: var(--color-text-muted);
		cursor: not-allowed;
		resize: none;
	}

	.textarea--error {
		border-color: var(--color-danger);
	}

	.textarea--error:focus {
		box-shadow: 0 0 0 3px rgba(201, 42, 42, 0.2);
	}

	.textarea--auto-resize {
		resize: none;
		overflow: hidden;
	}

	.textarea__footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		min-height: 20px;
	}

	.textarea__error {
		font-size: var(--font-size-sm);
		color: var(--color-danger);
	}

	.textarea__hint {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.textarea__count {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
		font-variant-numeric: tabular-nums;
	}

	.textarea__count--limit {
		color: var(--color-danger);
	}
</style>
