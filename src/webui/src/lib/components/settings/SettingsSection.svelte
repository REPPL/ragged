<!--
  Settings Section Component
  ragged WebUI v0.7.3

  Wrapper for settings section
-->
<script lang="ts">
	export let title: string;
	export let description = '';
</script>

<section class="settings-section">
	<div class="settings-section__header">
		<h2 class="settings-section__title">{title}</h2>
		{#if description}
			<p class="settings-section__description">{description}</p>
		{/if}
	</div>

	<div class="settings-section__content">
		<slot />
	</div>
</section>

<style>
	.settings-section {
		padding: var(--space-6);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
	}

	.settings-section__header {
		margin-bottom: var(--space-5);
		padding-bottom: var(--space-4);
		border-bottom: 1px solid var(--color-border-light);
	}

	.settings-section__title {
		margin: 0;
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
	}

	.settings-section__description {
		margin: var(--space-2) 0 0;
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.settings-section__content {
		display: flex;
		flex-direction: column;
		gap: var(--space-5);
	}
</style>
