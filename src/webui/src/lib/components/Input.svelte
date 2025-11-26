<!--
  Input Component
  ragged WebUI v0.7.3

  Usage:
  <Input type="text" bind:value={name} placeholder="Enter name" />
-->
<script lang="ts">
	import type { HTMLInputAttributes } from 'svelte/elements';
	import type { InputType } from '$types';

	interface $$Props extends Omit<HTMLInputAttributes, 'type'> {
		type?: InputType;
		value?: string;
		label?: string;
		error?: string;
		hint?: string;
		iconLeft?: string;
		iconRight?: string;
	}

	export let type: InputType = 'text';
	export let value = '';
	export let label: string | undefined = undefined;
	export let error: string | undefined = undefined;
	export let hint: string | undefined = undefined;
	export let iconLeft: string | undefined = undefined;
	export let iconRight: string | undefined = undefined;

	const id = $$restProps.id || `input-${Math.random().toString(36).slice(2, 9)}`;

	$: hasError = !!error;
</script>

<div class="input-wrapper">
	{#if label}
		<label for={id} class="input__label">
			{label}
			{#if $$restProps.required}
				<span class="input__required" aria-hidden="true">*</span>
			{/if}
		</label>
	{/if}

	<div class="input__container" class:input__container--error={hasError}>
		{#if iconLeft}
			<span class="input__icon input__icon--left" aria-hidden="true">
				{iconLeft}
			</span>
		{/if}

		<input
			{id}
			{type}
			bind:value
			class="input"
			class:input--has-icon-left={iconLeft}
			class:input--has-icon-right={iconRight}
			aria-invalid={hasError}
			aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
			{...$$restProps}
			on:input
			on:change
			on:focus
			on:blur
			on:keydown
			on:keyup
		/>

		{#if iconRight}
			<span class="input__icon input__icon--right" aria-hidden="true">
				{iconRight}
			</span>
		{/if}
	</div>

	{#if error}
		<p id="{id}-error" class="input__error" role="alert">
			{error}
		</p>
	{:else if hint}
		<p id="{id}-hint" class="input__hint">
			{hint}
		</p>
	{/if}
</div>

<style>
	.input-wrapper {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
		width: 100%;
	}

	.input__label {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-primary);
	}

	.input__required {
		color: var(--color-danger);
		margin-left: var(--space-1);
	}

	.input__container {
		position: relative;
		display: flex;
		align-items: center;
	}

	.input {
		width: 100%;
		height: 40px;
		padding: 0 var(--space-3);
		font-family: var(--font-sans);
		font-size: var(--font-size-base);
		color: var(--color-text-primary);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-medium);
		border-radius: var(--radius-md);
		transition:
			border-color var(--transition-fast),
			box-shadow var(--transition-fast);
	}

	.input::placeholder {
		color: var(--color-text-muted);
	}

	.input:hover:not(:disabled) {
		border-color: var(--color-border-dark);
	}

	.input:focus {
		outline: none;
		border-color: var(--color-primary);
		box-shadow: var(--shadow-focus);
	}

	.input:disabled {
		background-color: var(--color-bg-secondary);
		color: var(--color-text-muted);
		cursor: not-allowed;
	}

	.input--has-icon-left {
		padding-left: 40px;
	}

	.input--has-icon-right {
		padding-right: 40px;
	}

	.input__container--error .input {
		border-color: var(--color-danger);
	}

	.input__container--error .input:focus {
		box-shadow: 0 0 0 3px rgba(201, 42, 42, 0.2);
	}

	.input__icon {
		position: absolute;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 100%;
		color: var(--color-text-muted);
		pointer-events: none;
	}

	.input__icon--left {
		left: 0;
	}

	.input__icon--right {
		right: 0;
	}

	.input__error {
		font-size: var(--font-size-sm);
		color: var(--color-danger);
	}

	.input__hint {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}
</style>
