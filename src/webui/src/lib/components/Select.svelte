<!--
  Select Component
  ragged WebUI v0.7.3

  Usage:
  <Select bind:value={selected} options={items} placeholder="Select..." />
-->
<script lang="ts">
	import type { HTMLSelectAttributes } from 'svelte/elements';

	interface Option {
		value: string;
		label: string;
		disabled?: boolean;
	}

	interface $$Props extends Omit<HTMLSelectAttributes, 'value'> {
		value?: string;
		options: Option[];
		label?: string;
		error?: string;
		hint?: string;
		placeholder?: string;
	}

	export let value = '';
	export let options: Option[] = [];
	export let label: string | undefined = undefined;
	export let error: string | undefined = undefined;
	export let hint: string | undefined = undefined;
	export let placeholder: string | undefined = undefined;

	const id = $$restProps.id || `select-${Math.random().toString(36).slice(2, 9)}`;

	$: hasError = !!error;
</script>

<div class="select-wrapper">
	{#if label}
		<label for={id} class="select__label">
			{label}
			{#if $$restProps.required}
				<span class="select__required" aria-hidden="true">*</span>
			{/if}
		</label>
	{/if}

	<div class="select__container" class:select__container--error={hasError}>
		<select
			{id}
			bind:value
			class="select"
			aria-invalid={hasError}
			aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
			{...$$restProps}
			on:change
			on:focus
			on:blur
		>
			{#if placeholder}
				<option value="" disabled selected={!value}>{placeholder}</option>
			{/if}
			{#each options as option}
				<option value={option.value} disabled={option.disabled}>
					{option.label}
				</option>
			{/each}
		</select>

		<span class="select__icon" aria-hidden="true">
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<polyline points="6 9 12 15 18 9" />
			</svg>
		</span>
	</div>

	{#if error}
		<p id="{id}-error" class="select__error" role="alert">
			{error}
		</p>
	{:else if hint}
		<p id="{id}-hint" class="select__hint">
			{hint}
		</p>
	{/if}
</div>

<style>
	.select-wrapper {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
		width: 100%;
	}

	.select__label {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-primary);
	}

	.select__required {
		color: var(--color-danger);
		margin-left: var(--space-1);
	}

	.select__container {
		position: relative;
		display: flex;
		align-items: center;
	}

	.select {
		width: 100%;
		height: 40px;
		padding: 0 40px 0 var(--space-3);
		font-family: var(--font-sans);
		font-size: var(--font-size-base);
		color: var(--color-text-primary);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-medium);
		border-radius: var(--radius-md);
		cursor: pointer;
		appearance: none;
		transition:
			border-color var(--transition-fast),
			box-shadow var(--transition-fast);
	}

	.select:hover:not(:disabled) {
		border-color: var(--color-border-dark);
	}

	.select:focus {
		outline: none;
		border-color: var(--color-primary);
		box-shadow: var(--shadow-focus);
	}

	.select:disabled {
		background-color: var(--color-bg-secondary);
		color: var(--color-text-muted);
		cursor: not-allowed;
	}

	.select__container--error .select {
		border-color: var(--color-danger);
	}

	.select__container--error .select:focus {
		box-shadow: 0 0 0 3px rgba(201, 42, 42, 0.2);
	}

	.select__icon {
		position: absolute;
		right: var(--space-3);
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--color-text-muted);
		pointer-events: none;
	}

	.select__error {
		font-size: var(--font-size-sm);
		color: var(--color-danger);
	}

	.select__hint {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}
</style>
