<!--
  Collection Form Component
  ragged WebUI v0.7.3

  Form for creating/editing collections
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { Collection } from '$types';
	import Input from '../Input.svelte';
	import TextArea from '../TextArea.svelte';
	import Button from '../Button.svelte';

	export let collection: Partial<Collection> | null = null;
	export let loading = false;

	const dispatch = createEventDispatcher<{
		submit: { name: string; description: string };
		cancel: void;
	}>();

	let name = collection?.name ?? '';
	let description = collection?.description ?? '';
	let nameError = '';

	$: isEditing = !!collection?.id;
	$: canSubmit = name.trim().length > 0 && !loading;

	function validateName() {
		if (!name.trim()) {
			nameError = 'Collection name is required';
			return false;
		}
		if (name.length < 2) {
			nameError = 'Name must be at least 2 characters';
			return false;
		}
		if (name.length > 100) {
			nameError = 'Name must be less than 100 characters';
			return false;
		}
		if (!/^[a-zA-Z0-9_-]+$/.test(name)) {
			nameError = 'Name can only contain letters, numbers, underscores, and hyphens';
			return false;
		}
		nameError = '';
		return true;
	}

	function handleSubmit() {
		if (validateName() && canSubmit) {
			dispatch('submit', {
				name: name.trim(),
				description: description.trim()
			});
		}
	}

	function handleCancel() {
		dispatch('cancel');
	}
</script>

<form class="collection-form" on:submit|preventDefault={handleSubmit}>
	<div class="collection-form__field">
		<Input
			bind:value={name}
			label="Collection name"
			placeholder="my-collection"
			error={nameError}
			required
			on:blur={validateName}
		/>
		<p class="collection-form__hint">
			Use lowercase letters, numbers, underscores, or hyphens
		</p>
	</div>

	<div class="collection-form__field">
		<TextArea
			bind:value={description}
			label="Description"
			placeholder="Optional description for this collection..."
			rows={3}
			maxLength={500}
		/>
	</div>

	<div class="collection-form__actions">
		<Button variant="ghost" type="button" on:click={handleCancel}>
			Cancel
		</Button>
		<Button variant="primary" type="submit" {loading} disabled={!canSubmit}>
			{isEditing ? 'Save changes' : 'Create collection'}
		</Button>
	</div>
</form>

<style>
	.collection-form {
		display: flex;
		flex-direction: column;
		gap: var(--space-5);
	}

	.collection-form__field {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.collection-form__hint {
		margin: 0;
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.collection-form__actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--space-3);
		margin-top: var(--space-4);
		padding-top: var(--space-4);
		border-top: 1px solid var(--color-border-light);
	}
</style>
