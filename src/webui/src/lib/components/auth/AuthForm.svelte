<!--
  Auth Form Component
  ragged WebUI v0.7.3

  Base authentication form with validation
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import Input from '../Input.svelte';
	import Button from '../Button.svelte';

	export let mode: 'login' | 'register' = 'login';
	export let loading = false;
	export let error: string | null = null;

	const dispatch = createEventDispatcher<{
		submit: {
			email: string;
			password: string;
			name?: string;
		};
	}>();

	let email = '';
	let password = '';
	let confirmPassword = '';
	let name = '';

	let emailError = '';
	let passwordError = '';
	let confirmPasswordError = '';
	let nameError = '';

	function validateEmail(): boolean {
		if (!email.trim()) {
			emailError = 'Email is required';
			return false;
		}
		if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
			emailError = 'Please enter a valid email address';
			return false;
		}
		emailError = '';
		return true;
	}

	function validatePassword(): boolean {
		if (!password) {
			passwordError = 'Password is required';
			return false;
		}
		if (mode === 'register' && password.length < 8) {
			passwordError = 'Password must be at least 8 characters';
			return false;
		}
		passwordError = '';
		return true;
	}

	function validateConfirmPassword(): boolean {
		if (mode !== 'register') return true;
		if (password !== confirmPassword) {
			confirmPasswordError = 'Passwords do not match';
			return false;
		}
		confirmPasswordError = '';
		return true;
	}

	function validateName(): boolean {
		if (mode !== 'register') return true;
		if (!name.trim()) {
			nameError = 'Name is required';
			return false;
		}
		if (name.length < 2) {
			nameError = 'Name must be at least 2 characters';
			return false;
		}
		nameError = '';
		return true;
	}

	function handleSubmit() {
		const isEmailValid = validateEmail();
		const isPasswordValid = validatePassword();
		const isConfirmValid = validateConfirmPassword();
		const isNameValid = validateName();

		if (isEmailValid && isPasswordValid && isConfirmValid && isNameValid) {
			dispatch('submit', {
				email: email.trim(),
				password,
				...(mode === 'register' ? { name: name.trim() } : {})
			});
		}
	}
</script>

<form class="auth-form" on:submit|preventDefault={handleSubmit}>
	{#if error}
		<div class="auth-form__error" role="alert">
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<circle cx="12" cy="12" r="10" />
				<path d="M12 8v4M12 16h.01" />
			</svg>
			{error}
		</div>
	{/if}

	{#if mode === 'register'}
		<div class="auth-form__field">
			<Input
				bind:value={name}
				type="text"
				label="Name"
				placeholder="Your name"
				error={nameError}
				autocomplete="name"
				required
				on:blur={validateName}
			/>
		</div>
	{/if}

	<div class="auth-form__field">
		<Input
			bind:value={email}
			type="email"
			label="Email"
			placeholder="you@example.com"
			error={emailError}
			autocomplete="email"
			required
			on:blur={validateEmail}
		/>
	</div>

	<div class="auth-form__field">
		<Input
			bind:value={password}
			type="password"
			label="Password"
			placeholder={mode === 'register' ? 'At least 8 characters' : 'Your password'}
			error={passwordError}
			autocomplete={mode === 'login' ? 'current-password' : 'new-password'}
			required
			on:blur={validatePassword}
		/>
	</div>

	{#if mode === 'register'}
		<div class="auth-form__field">
			<Input
				bind:value={confirmPassword}
				type="password"
				label="Confirm Password"
				placeholder="Confirm your password"
				error={confirmPasswordError}
				autocomplete="new-password"
				required
				on:blur={validateConfirmPassword}
			/>
		</div>
	{/if}

	<Button
		type="submit"
		variant="primary"
		size="lg"
		fullWidth
		{loading}
		disabled={loading}
	>
		{#if loading}
			{mode === 'login' ? 'Signing in...' : 'Creating account...'}
		{:else}
			{mode === 'login' ? 'Sign in' : 'Create account'}
		{/if}
	</Button>
</form>

<style>
	.auth-form {
		display: flex;
		flex-direction: column;
		gap: var(--space-5);
	}

	.auth-form__error {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-3) var(--space-4);
		font-size: var(--font-size-sm);
		color: var(--color-danger);
		background-color: var(--color-danger-light);
		border-radius: var(--radius-md);
	}

	.auth-form__field {
		display: flex;
		flex-direction: column;
	}
</style>
