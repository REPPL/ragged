<!--
  Settings Page
  ragged WebUI v0.9.0

  Application settings interface with theme selection
  WCAG 2.1 AA compliant high-contrast modes
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import type { UserSettings } from '$types';
	import { addToast, theme } from '$stores';
	import { api } from '$api';
	import { SettingsSection, SettingsRow, Toggle, ThemePreview } from '$lib/components/settings';
	import type { ThemeMode } from '$lib/stores/theme';
	import Select from '$lib/components/Select.svelte';
	import Input from '$lib/components/Input.svelte';
	import Button from '$lib/components/Button.svelte';
	import Skeleton from '$lib/components/Skeleton.svelte';

	let settings: UserSettings | null = null;
	let loading = true;
	let saving = false;
	let error: string | null = null;

	// Local state for form
	let localTheme: 'light' | 'dark' | 'high-contrast' | 'high-contrast-dark' | 'system' = 'system';
	let sidebarCollapsed = false;
	let animations = true;
	let defaultTopK = 5;
	let defaultRetrievalMethod: 'vector' | 'bm25' | 'hybrid' = 'hybrid';
	let streamResponses = true;
	let enableQueryHistory = true;

	const themeOptions = [
		{ value: 'light', label: 'Light' },
		{ value: 'dark', label: 'Dark' },
		{ value: 'high-contrast', label: 'High Contrast' },
		{ value: 'high-contrast-dark', label: 'High Contrast Dark' },
		{ value: 'system', label: 'System' }
	];

	const topKOptions = [
		{ value: '3', label: '3 results' },
		{ value: '5', label: '5 results' },
		{ value: '10', label: '10 results' },
		{ value: '20', label: '20 results' }
	];

	const retrievalOptions = [
		{ value: 'hybrid', label: 'Hybrid (recommended)' },
		{ value: 'vector', label: 'Vector only' },
		{ value: 'bm25', label: 'BM25 only' }
	];

	async function loadSettings() {
		loading = true;
		error = null;
		try {
			settings = await api.settings.get();
			// Populate local state
			localTheme = settings.general.theme;
			sidebarCollapsed = settings.general.sidebarCollapsed;
			animations = settings.general.animations;
			defaultTopK = settings.query.defaultTopK;
			defaultRetrievalMethod = settings.query.defaultRetrievalMethod;
			streamResponses = settings.query.streamResponses;
			enableQueryHistory = settings.privacy.enableQueryHistory;
		} catch (err) {
			// If settings don't exist, use defaults
			console.log('Using default settings');
		} finally {
			loading = false;
		}
	}

	async function saveSettings() {
		saving = true;
		try {
			const updatedSettings: Partial<UserSettings> = {
				general: {
					theme: localTheme,
					sidebarCollapsed,
					animations
				},
				query: {
					defaultTopK,
					defaultRetrievalMethod,
					autoSubmitOnEnter: true,
					showAdvancedOptions: false,
					streamResponses
				},
				privacy: {
					enableQueryHistory,
					enableTelemetry: false
				}
			};

			await api.settings.update(updatedSettings);

			// Apply theme immediately
			theme.setTheme(localTheme);

			addToast({
				type: 'success',
				title: 'Settings saved',
				message: 'Your preferences have been updated'
			});
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to save settings';
			addToast({
				type: 'error',
				title: 'Save failed',
				message
			});
		} finally {
			saving = false;
		}
	}

	function handleThemeChange(event: Event) {
		const target = event.target as HTMLSelectElement;
		localTheme = target.value as ThemeMode;
		// Apply immediately for preview
		theme.setTheme(localTheme);
	}

	function handleThemeSelect(selectedTheme: ThemeMode) {
		localTheme = selectedTheme;
		// Apply immediately for preview
		theme.setTheme(localTheme);
	}

	function handleTopKChange(event: Event) {
		const target = event.target as HTMLSelectElement;
		defaultTopK = parseInt(target.value, 10);
	}

	function handleRetrievalChange(event: Event) {
		const target = event.target as HTMLSelectElement;
		defaultRetrievalMethod = target.value as 'vector' | 'bm25' | 'hybrid';
	}

	onMount(() => {
		loadSettings();
	});
</script>

<svelte:head>
	<title>Settings - ragged</title>
</svelte:head>

<div class="settings-page">
	<div class="settings-page__header">
		<h1 class="settings-page__title">Settings</h1>
		<p class="settings-page__subtitle">
			Configure your preferences
		</p>
	</div>

	{#if loading}
		<div class="settings-page__loading">
			{#each Array(3) as _}
				<Skeleton height="200px" />
			{/each}
		</div>
	{:else}
		<div class="settings-page__sections">
			<!-- Appearance -->
			<SettingsSection title="Appearance" description="Customise how ragged looks">
				<div class="theme-selection">
					<div class="theme-selection__header">
						<span class="theme-selection__label">Theme</span>
						<span class="theme-selection__description">
							Choose your preferred colour scheme. High contrast modes are WCAG 2.1 AA compliant.
						</span>
					</div>
					<ThemePreview
						currentTheme={localTheme}
						onSelect={handleThemeSelect}
					/>
				</div>

				<SettingsRow
					label="Animations"
					description="Enable smooth animations and transitions"
				>
					<Toggle
						bind:checked={animations}
						label="Enable animations"
					/>
				</SettingsRow>

				<SettingsRow
					label="Compact sidebar"
					description="Start with the sidebar collapsed"
				>
					<Toggle
						bind:checked={sidebarCollapsed}
						label="Collapse sidebar by default"
					/>
				</SettingsRow>
			</SettingsSection>

			<!-- Query Defaults -->
			<SettingsSection title="Query Defaults" description="Default settings for search queries">
				<SettingsRow
					label="Results count"
					description="Default number of results to return"
					htmlFor="topk-select"
				>
					<Select
						id="topk-select"
						value={String(defaultTopK)}
						options={topKOptions}
						on:change={handleTopKChange}
					/>
				</SettingsRow>

				<SettingsRow
					label="Retrieval method"
					description="Default search algorithm to use"
					htmlFor="retrieval-select"
				>
					<Select
						id="retrieval-select"
						value={defaultRetrievalMethod}
						options={retrievalOptions}
						on:change={handleRetrievalChange}
					/>
				</SettingsRow>

				<SettingsRow
					label="Stream responses"
					description="Show answers as they are generated"
				>
					<Toggle
						bind:checked={streamResponses}
						label="Enable streaming"
					/>
				</SettingsRow>
			</SettingsSection>

			<!-- Privacy -->
			<SettingsSection title="Privacy" description="Control your data and privacy settings">
				<SettingsRow
					label="Query history"
					description="Save your query history locally for quick access"
				>
					<Toggle
						bind:checked={enableQueryHistory}
						label="Enable query history"
					/>
				</SettingsRow>

				<SettingsRow
					label="Local processing"
					description="All data is processed locally - nothing is sent to external servers"
				>
					<span class="settings-page__badge">Always on</span>
				</SettingsRow>
			</SettingsSection>

			<!-- About -->
			<SettingsSection title="About" description="Information about ragged">
				<SettingsRow label="Version">
					<span class="settings-page__version">v0.9.0</span>
				</SettingsRow>

				<SettingsRow label="Documentation">
					<a
						href="https://github.com/ragged/ragged"
						target="_blank"
						rel="noopener noreferrer"
						class="settings-page__link"
					>
						View documentation
						<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3" />
						</svg>
					</a>
				</SettingsRow>

				<SettingsRow label="License">
					<span class="settings-page__license">GPL-3.0</span>
				</SettingsRow>
			</SettingsSection>
		</div>

		<div class="settings-page__actions">
			<Button variant="ghost" on:click={loadSettings}>
				Reset
			</Button>
			<Button variant="primary" loading={saving} on:click={saveSettings}>
				Save changes
			</Button>
		</div>
	{/if}
</div>

<style>
	.settings-page {
		display: flex;
		flex-direction: column;
		gap: var(--space-6);
		max-width: 800px;
		margin: 0 auto;
	}

	.settings-page__header {
		margin-bottom: var(--space-2);
	}

	.settings-page__title {
		margin: 0;
		font-size: var(--font-size-3xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-text-primary);
	}

	.settings-page__subtitle {
		margin: var(--space-2) 0 0;
		font-size: var(--font-size-lg);
		color: var(--color-text-muted);
	}

	.settings-page__loading {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
	}

	.settings-page__sections {
		display: flex;
		flex-direction: column;
		gap: var(--space-6);
	}

	.settings-page__actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--space-3);
		padding-top: var(--space-4);
		border-top: 1px solid var(--color-border-light);
	}

	.settings-page__badge {
		display: inline-flex;
		align-items: center;
		padding: var(--space-1) var(--space-2);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium);
		color: var(--color-success);
		background-color: var(--color-success-light);
		border-radius: var(--radius-md);
	}

	.settings-page__version {
		font-family: var(--font-mono);
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
	}

	.settings-page__link {
		display: inline-flex;
		align-items: center;
		gap: var(--space-1);
		font-size: var(--font-size-sm);
		color: var(--color-primary);
		text-decoration: none;
	}

	.settings-page__link:hover {
		text-decoration: underline;
	}

	.settings-page__license {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
	}

	.theme-selection {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
	}

	.theme-selection__header {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.theme-selection__label {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-primary);
	}

	.theme-selection__description {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}
</style>
