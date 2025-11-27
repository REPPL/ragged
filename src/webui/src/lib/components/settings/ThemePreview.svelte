<!--
  Theme Preview Component
  ragged WebUI v0.9.0

  Visual theme previews for the settings page
  WCAG 2.1 AA compliant
-->
<script lang="ts">
	import type { ThemeMode } from '$lib/stores/theme';
	import { getThemeLabel } from '$stores';

	export let currentTheme: ThemeMode = 'system';
	export let onSelect: (theme: ThemeMode) => void = () => {};

	const themes: ThemeMode[] = ['light', 'dark', 'high-contrast', 'high-contrast-dark', 'system'];

	interface ThemeStyle {
		bg: string;
		text: string;
		accent: string;
		border: string;
	}

	const themeStyles: Record<ThemeMode, ThemeStyle> = {
		light: {
			bg: '#ffffff',
			text: '#1a1a2e',
			accent: '#4f46e5',
			border: '#e2e8f0'
		},
		dark: {
			bg: '#1a1a2e',
			text: '#f8fafc',
			accent: '#818cf8',
			border: '#334155'
		},
		'high-contrast': {
			bg: '#ffffff',
			text: '#000000',
			accent: '#0066cc',
			border: '#000000'
		},
		'high-contrast-dark': {
			bg: '#000000',
			text: '#ffffff',
			accent: '#66b3ff',
			border: '#ffffff'
		},
		system: {
			bg: 'linear-gradient(135deg, #ffffff 50%, #1a1a2e 50%)',
			text: '#1a1a2e',
			accent: '#4f46e5',
			border: '#e2e8f0'
		}
	};

	function handleKeyDown(event: KeyboardEvent, theme: ThemeMode) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			onSelect(theme);
		}
	}
</script>

<div class="theme-preview" role="radiogroup" aria-label="Theme selection">
	{#each themes as theme}
		{@const style = themeStyles[theme]}
		{@const isSelected = currentTheme === theme}
		<button
			type="button"
			class="theme-preview__card"
			class:theme-preview__card--selected={isSelected}
			style="--preview-bg: {style.bg}; --preview-text: {style.text}; --preview-accent: {style.accent}; --preview-border: {style.border}"
			on:click={() => onSelect(theme)}
			on:keydown={(e) => handleKeyDown(e, theme)}
			role="radio"
			aria-checked={isSelected}
			aria-label="{getThemeLabel(theme)} theme"
		>
			<div class="theme-preview__mockup">
				{#if theme === 'system'}
					<div class="theme-preview__split">
						<div class="theme-preview__split-light">
							<div class="theme-preview__header-bar" style="background: #e2e8f0"></div>
							<div class="theme-preview__content-lines">
								<div class="theme-preview__line" style="background: #1a1a2e; width: 70%"></div>
								<div class="theme-preview__line" style="background: #94a3b8; width: 50%"></div>
							</div>
						</div>
						<div class="theme-preview__split-dark">
							<div class="theme-preview__header-bar" style="background: #334155"></div>
							<div class="theme-preview__content-lines">
								<div class="theme-preview__line" style="background: #f8fafc; width: 70%"></div>
								<div class="theme-preview__line" style="background: #64748b; width: 50%"></div>
							</div>
						</div>
					</div>
				{:else}
					<div class="theme-preview__header-bar"></div>
					<div class="theme-preview__content-lines">
						<div class="theme-preview__line theme-preview__line--primary"></div>
						<div class="theme-preview__line theme-preview__line--secondary"></div>
						<div class="theme-preview__line theme-preview__line--accent"></div>
					</div>
				{/if}
			</div>
			<span class="theme-preview__label">{getThemeLabel(theme)}</span>
			{#if isSelected}
				<span class="theme-preview__check" aria-hidden="true">
					<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
						<polyline points="20 6 9 17 4 12" />
					</svg>
				</span>
			{/if}
		</button>
	{/each}
</div>

<style>
	.theme-preview {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
		gap: var(--space-3);
		width: 100%;
	}

	.theme-preview__card {
		position: relative;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-3);
		background: var(--color-bg-elevated);
		border: 2px solid var(--color-border-light);
		border-radius: var(--radius-lg);
		cursor: pointer;
		transition: border-color 0.15s ease, box-shadow 0.15s ease;
	}

	.theme-preview__card:hover {
		border-color: var(--color-primary);
	}

	.theme-preview__card:focus-visible {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
	}

	.theme-preview__card--selected {
		border-color: var(--color-primary);
		box-shadow: 0 0 0 3px var(--color-primary-light);
	}

	.theme-preview__mockup {
		width: 100%;
		aspect-ratio: 4/3;
		background: var(--preview-bg);
		border: 1px solid var(--preview-border);
		border-radius: var(--radius-md);
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	.theme-preview__header-bar {
		height: 8px;
		background: var(--preview-border);
	}

	.theme-preview__content-lines {
		flex: 1;
		padding: 6px;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.theme-preview__line {
		height: 4px;
		border-radius: 2px;
	}

	.theme-preview__line--primary {
		width: 70%;
		background: var(--preview-text);
	}

	.theme-preview__line--secondary {
		width: 50%;
		background: var(--preview-text);
		opacity: 0.5;
	}

	.theme-preview__line--accent {
		width: 30%;
		background: var(--preview-accent);
	}

	.theme-preview__split {
		display: flex;
		height: 100%;
		width: 100%;
	}

	.theme-preview__split-light {
		flex: 1;
		background: #ffffff;
		display: flex;
		flex-direction: column;
	}

	.theme-preview__split-dark {
		flex: 1;
		background: #1a1a2e;
		display: flex;
		flex-direction: column;
	}

	.theme-preview__label {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-primary);
		text-align: center;
	}

	.theme-preview__check {
		position: absolute;
		top: var(--space-2);
		right: var(--space-2);
		width: 20px;
		height: 20px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--color-primary);
		color: white;
		border-radius: 50%;
	}

	@media (max-width: 480px) {
		.theme-preview {
			grid-template-columns: repeat(2, 1fr);
		}
	}
</style>
