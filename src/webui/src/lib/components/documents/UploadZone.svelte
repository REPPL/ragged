<!--
  Upload Zone Component
  ragged WebUI v0.7.3

  Drag-and-drop file upload area with progress tracking
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import Progress from '../Progress.svelte';

	export let accept = '.pdf,.txt,.md,.markdown,.html,.json,.csv';
	export let multiple = true;
	export let maxSizeMB = 50;
	export let disabled = false;

	const dispatch = createEventDispatcher<{
		upload: { files: File[] };
		error: { message: string };
	}>();

	let dragActive = false;
	let uploading = false;
	let progress = 0;
	let fileInput: HTMLInputElement;

	const maxSizeBytes = maxSizeMB * 1024 * 1024;

	function handleDragEnter(e: DragEvent) {
		e.preventDefault();
		if (!disabled) {
			dragActive = true;
		}
	}

	function handleDragLeave(e: DragEvent) {
		e.preventDefault();
		dragActive = false;
	}

	function handleDragOver(e: DragEvent) {
		e.preventDefault();
	}

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragActive = false;

		if (disabled) return;

		const files = e.dataTransfer?.files;
		if (files && files.length > 0) {
			processFiles(Array.from(files));
		}
	}

	function handleFileSelect(e: Event) {
		const target = e.target as HTMLInputElement;
		if (target.files && target.files.length > 0) {
			processFiles(Array.from(target.files));
		}
	}

	function processFiles(files: File[]) {
		// Filter by accepted types
		const acceptedExtensions = accept.split(',').map((ext) => ext.trim().toLowerCase());
		const validFiles = files.filter((file) => {
			const ext = '.' + file.name.split('.').pop()?.toLowerCase();
			return acceptedExtensions.includes(ext);
		});

		if (validFiles.length !== files.length) {
			const invalidCount = files.length - validFiles.length;
			dispatch('error', {
				message: `${invalidCount} file(s) were skipped due to unsupported format`
			});
		}

		// Check file sizes
		const oversizedFiles = validFiles.filter((file) => file.size > maxSizeBytes);
		if (oversizedFiles.length > 0) {
			dispatch('error', {
				message: `${oversizedFiles.length} file(s) exceed the ${maxSizeMB}MB limit`
			});
			return;
		}

		if (validFiles.length === 0) {
			dispatch('error', { message: 'No valid files to upload' });
			return;
		}

		// Dispatch upload event
		dispatch('upload', { files: validFiles });

		// Reset input
		if (fileInput) {
			fileInput.value = '';
		}
	}

	function openFilePicker() {
		if (!disabled) {
			fileInput?.click();
		}
	}

	function formatAcceptedTypes(): string {
		return accept
			.split(',')
			.map((ext) => ext.trim().replace('.', '').toUpperCase())
			.join(', ');
	}
</script>

<div
	class="upload-zone"
	class:upload-zone--active={dragActive}
	class:upload-zone--disabled={disabled}
	class:upload-zone--uploading={uploading}
	on:dragenter={handleDragEnter}
	on:dragleave={handleDragLeave}
	on:dragover={handleDragOver}
	on:drop={handleDrop}
	on:click={openFilePicker}
	on:keydown={(e) => e.key === 'Enter' && openFilePicker()}
	role="button"
	tabindex={disabled ? -1 : 0}
	aria-label="Upload files"
>
	<input
		bind:this={fileInput}
		type="file"
		{accept}
		{multiple}
		{disabled}
		on:change={handleFileSelect}
		class="upload-zone__input"
		aria-hidden="true"
	/>

	{#if uploading}
		<div class="upload-zone__progress">
			<Progress value={progress} max={100} showLabel />
			<p class="upload-zone__progress-text">Uploading...</p>
		</div>
	{:else}
		<div class="upload-zone__content">
			<svg
				class="upload-zone__icon"
				width="48"
				height="48"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="1.5"
			>
				<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
				<polyline points="17 8 12 3 7 8" />
				<line x1="12" y1="3" x2="12" y2="15" />
			</svg>

			<div class="upload-zone__text">
				<p class="upload-zone__title">
					{#if dragActive}
						Drop files here
					{:else}
						Drag & drop files here
					{/if}
				</p>
				<p class="upload-zone__subtitle">
					or <span class="upload-zone__link">browse files</span>
				</p>
			</div>

			<p class="upload-zone__hint">
				Accepted: {formatAcceptedTypes()} (max {maxSizeMB}MB)
			</p>
		</div>
	{/if}
</div>

<style>
	.upload-zone {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 200px;
		padding: var(--space-6);
		background-color: var(--color-bg-secondary);
		border: 2px dashed var(--color-border-medium);
		border-radius: var(--radius-lg);
		cursor: pointer;
		transition:
			border-color var(--transition-fast),
			background-color var(--transition-fast);
	}

	.upload-zone:hover:not(.upload-zone--disabled) {
		border-color: var(--color-primary);
		background-color: var(--color-primary-light);
	}

	.upload-zone--active {
		border-color: var(--color-primary);
		background-color: var(--color-primary-light);
	}

	.upload-zone--disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.upload-zone--uploading {
		cursor: default;
	}

	.upload-zone__input {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border: 0;
	}

	.upload-zone__content {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-4);
		text-align: center;
	}

	.upload-zone__icon {
		color: var(--color-text-muted);
		transition: color var(--transition-fast);
	}

	.upload-zone:hover:not(.upload-zone--disabled) .upload-zone__icon {
		color: var(--color-primary);
	}

	.upload-zone__text {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.upload-zone__title {
		margin: 0;
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
	}

	.upload-zone__subtitle {
		margin: 0;
		font-size: var(--font-size-base);
		color: var(--color-text-secondary);
	}

	.upload-zone__link {
		color: var(--color-primary);
		text-decoration: underline;
	}

	.upload-zone__hint {
		margin: 0;
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.upload-zone__progress {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-3);
		width: 100%;
		max-width: 300px;
	}

	.upload-zone__progress-text {
		margin: 0;
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
	}
</style>
