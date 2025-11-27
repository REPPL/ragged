<!--
  Date Range Picker Component
  ragged WebUI v0.9.2

  Date range selection with presets
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import Button from '../Button.svelte';

	export let startDate: Date | null = null;
	export let endDate: Date | null = null;
	export let label = 'Date range';

	const dispatch = createEventDispatcher<{
		change: { start: Date | null; end: Date | null };
	}>();

	let showPicker = false;
	let tempStart = startDate ? formatDateForInput(startDate) : '';
	let tempEnd = endDate ? formatDateForInput(endDate) : '';

	interface Preset {
		label: string;
		getValue: () => { start: Date; end: Date };
	}

	const presets: Preset[] = [
		{
			label: 'Today',
			getValue: () => {
				const today = new Date();
				today.setHours(0, 0, 0, 0);
				const end = new Date();
				end.setHours(23, 59, 59, 999);
				return { start: today, end };
			}
		},
		{
			label: 'Yesterday',
			getValue: () => {
				const yesterday = new Date();
				yesterday.setDate(yesterday.getDate() - 1);
				yesterday.setHours(0, 0, 0, 0);
				const end = new Date(yesterday);
				end.setHours(23, 59, 59, 999);
				return { start: yesterday, end };
			}
		},
		{
			label: 'Last 7 days',
			getValue: () => {
				const end = new Date();
				end.setHours(23, 59, 59, 999);
				const start = new Date();
				start.setDate(start.getDate() - 7);
				start.setHours(0, 0, 0, 0);
				return { start, end };
			}
		},
		{
			label: 'Last 30 days',
			getValue: () => {
				const end = new Date();
				end.setHours(23, 59, 59, 999);
				const start = new Date();
				start.setDate(start.getDate() - 30);
				start.setHours(0, 0, 0, 0);
				return { start, end };
			}
		},
		{
			label: 'This month',
			getValue: () => {
				const now = new Date();
				const start = new Date(now.getFullYear(), now.getMonth(), 1);
				const end = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59, 999);
				return { start, end };
			}
		},
		{
			label: 'Last month',
			getValue: () => {
				const now = new Date();
				const start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
				const end = new Date(now.getFullYear(), now.getMonth(), 0, 23, 59, 59, 999);
				return { start, end };
			}
		}
	];

	function formatDateForInput(date: Date): string {
		return date.toISOString().split('T')[0];
	}

	function formatDateDisplay(date: Date | null): string {
		if (!date) return '';
		return date.toLocaleDateString('en-GB', {
			day: 'numeric',
			month: 'short',
			year: 'numeric'
		});
	}

	function applyPreset(preset: Preset) {
		const { start, end } = preset.getValue();
		tempStart = formatDateForInput(start);
		tempEnd = formatDateForInput(end);
		applyRange();
	}

	function applyRange() {
		const start = tempStart ? new Date(tempStart) : null;
		const end = tempEnd ? new Date(tempEnd) : null;

		if (end) {
			end.setHours(23, 59, 59, 999);
		}

		startDate = start;
		endDate = end;
		showPicker = false;
		dispatch('change', { start, end });
	}

	function clearRange() {
		tempStart = '';
		tempEnd = '';
		startDate = null;
		endDate = null;
		showPicker = false;
		dispatch('change', { start: null, end: null });
	}

	function handleClickOutside(event: MouseEvent) {
		const target = event.target as HTMLElement;
		if (!target.closest('.date-range-picker')) {
			showPicker = false;
		}
	}

	$: displayText = startDate && endDate
		? `${formatDateDisplay(startDate)} - ${formatDateDisplay(endDate)}`
		: startDate
			? `From ${formatDateDisplay(startDate)}`
			: endDate
				? `Until ${formatDateDisplay(endDate)}`
				: 'Any time';

	$: hasValue = startDate || endDate;
</script>

<svelte:window on:click={handleClickOutside} />

<div class="date-range-picker">
	<button
		type="button"
		class="date-range-picker__trigger"
		class:date-range-picker__trigger--active={hasValue}
		on:click|stopPropagation={() => (showPicker = !showPicker)}
		aria-expanded={showPicker}
		aria-haspopup="dialog"
	>
		<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
			<rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
			<line x1="16" y1="2" x2="16" y2="6" />
			<line x1="8" y1="2" x2="8" y2="6" />
			<line x1="3" y1="10" x2="21" y2="10" />
		</svg>
		<span class="date-range-picker__text">{displayText}</span>
		{#if hasValue}
			<button
				type="button"
				class="date-range-picker__clear"
				on:click|stopPropagation={clearRange}
				aria-label="Clear date range"
			>
				<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="18" y1="6" x2="6" y2="18" />
					<line x1="6" y1="6" x2="18" y2="18" />
				</svg>
			</button>
		{/if}
	</button>

	{#if showPicker}
		<div
			class="date-range-picker__dropdown"
			role="dialog"
			aria-label="Select date range"
			on:click|stopPropagation
		>
			<div class="date-range-picker__presets">
				<p class="date-range-picker__section-title">Quick select</p>
				<div class="date-range-picker__preset-grid">
					{#each presets as preset}
						<button
							type="button"
							class="date-range-picker__preset"
							on:click={() => applyPreset(preset)}
						>
							{preset.label}
						</button>
					{/each}
				</div>
			</div>

			<div class="date-range-picker__custom">
				<p class="date-range-picker__section-title">Custom range</p>
				<div class="date-range-picker__inputs">
					<div class="date-range-picker__input-group">
						<label for="date-start">From</label>
						<input
							id="date-start"
							type="date"
							bind:value={tempStart}
							max={tempEnd || undefined}
						/>
					</div>
					<div class="date-range-picker__input-group">
						<label for="date-end">To</label>
						<input
							id="date-end"
							type="date"
							bind:value={tempEnd}
							min={tempStart || undefined}
						/>
					</div>
				</div>
			</div>

			<div class="date-range-picker__actions">
				<Button variant="ghost" size="sm" on:click={clearRange}>
					Clear
				</Button>
				<Button variant="primary" size="sm" on:click={applyRange}>
					Apply
				</Button>
			</div>
		</div>
	{/if}
</div>

<style>
	.date-range-picker {
		position: relative;
	}

	.date-range-picker__trigger {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-2) var(--space-3);
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: border-color var(--transition-fast), background-color var(--transition-fast);
	}

	.date-range-picker__trigger:hover {
		border-color: var(--color-border);
		background-color: var(--color-bg-secondary);
	}

	.date-range-picker__trigger--active {
		border-color: var(--color-primary);
		background-color: var(--color-primary-light);
		color: var(--color-primary);
	}

	.date-range-picker__text {
		white-space: nowrap;
	}

	.date-range-picker__clear {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2px;
		background: none;
		border: none;
		border-radius: var(--radius-sm);
		cursor: pointer;
		opacity: 0.7;
	}

	.date-range-picker__clear:hover {
		opacity: 1;
		background-color: rgba(0, 0, 0, 0.1);
	}

	.date-range-picker__dropdown {
		position: absolute;
		top: calc(100% + var(--space-2));
		left: 0;
		z-index: var(--z-dropdown);
		min-width: 320px;
		padding: var(--space-4);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-lg);
	}

	.date-range-picker__section-title {
		margin: 0 0 var(--space-2);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.date-range-picker__presets {
		margin-bottom: var(--space-4);
		padding-bottom: var(--space-4);
		border-bottom: 1px solid var(--color-border-light);
	}

	.date-range-picker__preset-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--space-2);
	}

	.date-range-picker__preset {
		padding: var(--space-2);
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		background: none;
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.date-range-picker__preset:hover {
		border-color: var(--color-primary);
		background-color: var(--color-primary-light);
		color: var(--color-primary);
	}

	.date-range-picker__custom {
		margin-bottom: var(--space-4);
	}

	.date-range-picker__inputs {
		display: flex;
		gap: var(--space-3);
	}

	.date-range-picker__input-group {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.date-range-picker__input-group label {
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.date-range-picker__input-group input {
		padding: var(--space-2);
		font-size: var(--font-size-sm);
		color: var(--color-text-primary);
		background-color: var(--color-bg);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
	}

	.date-range-picker__input-group input:focus {
		outline: none;
		border-color: var(--color-primary);
		box-shadow: 0 0 0 3px var(--color-primary-light);
	}

	.date-range-picker__actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--space-2);
	}
</style>
