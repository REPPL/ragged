<!--
  Settings Row Component
  ragged WebUI v0.9.0

  Individual setting row with label and control
-->
<script lang="ts">
	export let label: string;
	export let description = '';
	export let htmlFor = '';
</script>

<div class="settings-row">
	<div class="settings-row__info">
		<label class="settings-row__label" for={htmlFor || undefined}>{label}</label>
		{#if description}
			<p class="settings-row__description">{description}</p>
		{/if}
	</div>

	<div class="settings-row__control">
		<slot />
	</div>
</div>

<style>
	.settings-row {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: var(--space-4);
	}

	.settings-row__info {
		flex: 1;
		min-width: 0;
	}

	.settings-row__label {
		display: block;
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-primary);
	}

	.settings-row__description {
		margin: var(--space-1) 0 0;
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.settings-row__control {
		flex-shrink: 0;
	}

	@media (max-width: 640px) {
		.settings-row {
			flex-direction: column;
			gap: var(--space-2);
		}
	}
</style>
