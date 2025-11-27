<!--
  Toggle Component
  ragged WebUI v0.9.0

  On/off toggle switch
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let checked = false;
	export let disabled = false;
	export let id = '';
	export let label = '';

	const dispatch = createEventDispatcher<{
		change: { checked: boolean };
	}>();

	function handleChange() {
		if (!disabled) {
			checked = !checked;
			dispatch('change', { checked });
		}
	}
</script>

<button
	type="button"
	role="switch"
	aria-checked={checked}
	aria-label={label}
	{id}
	class="toggle"
	class:toggle--checked={checked}
	class:toggle--disabled={disabled}
	{disabled}
	on:click={handleChange}
>
	<span class="toggle__track">
		<span class="toggle__thumb" />
	</span>
</button>

<style>
	.toggle {
		display: inline-flex;
		padding: 0;
		background: none;
		border: none;
		cursor: pointer;
	}

	.toggle--disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.toggle__track {
		position: relative;
		width: 44px;
		height: 24px;
		background-color: var(--color-bg-tertiary);
		border-radius: var(--radius-full);
		transition: background-color var(--transition-fast);
	}

	.toggle--checked .toggle__track {
		background-color: var(--color-primary);
	}

	.toggle__thumb {
		position: absolute;
		top: 2px;
		left: 2px;
		width: 20px;
		height: 20px;
		background-color: var(--color-bg);
		border-radius: var(--radius-full);
		box-shadow: var(--shadow-sm);
		transition: transform var(--transition-fast);
	}

	.toggle--checked .toggle__thumb {
		transform: translateX(20px);
	}

	.toggle:focus-visible .toggle__track {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
	}
</style>
