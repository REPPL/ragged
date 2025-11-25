<!--
  Register Page
  ragged WebUI v0.7.3

  User registration interface
-->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { auth, addToast } from '$stores';
	import { AuthForm } from '$lib/components/auth';

	let loading = false;
	let error: string | null = null;

	async function handleSubmit(event: CustomEvent<{ email: string; password: string; name?: string }>) {
		loading = true;
		error = null;

		try {
			// In a real app, this would call the API
			const response = await fetch('/api/auth/register', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(event.detail),
				credentials: 'include'
			});

			if (!response.ok) {
				const data = await response.json();
				throw new Error(data.detail || 'Registration failed');
			}

			const userData = await response.json();
			auth.setUser(userData);

			addToast({
				type: 'success',
				title: 'Account created!',
				message: 'Welcome to ragged'
			});

			goto('/');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Registration failed';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Create account - ragged</title>
</svelte:head>

<div class="register-page">
	<div class="register-page__container">
		<div class="register-page__header">
			<h1 class="register-page__logo">ragged</h1>
			<p class="register-page__subtitle">Create your account</p>
		</div>

		<div class="register-page__form">
			<AuthForm
				mode="register"
				{loading}
				{error}
				on:submit={handleSubmit}
			/>
		</div>

		<div class="register-page__footer">
			<p class="register-page__text">
				Already have an account?
				<a href="/auth/login" class="register-page__link">Sign in</a>
			</p>
		</div>

		<div class="register-page__local-notice">
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
				<path d="M7 11V7a5 5 0 0110 0v4" />
			</svg>
			<span>All data stays local on your machine</span>
		</div>
	</div>
</div>

<style>
	.register-page {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 100vh;
		padding: var(--space-4);
		background-color: var(--color-bg-secondary);
	}

	.register-page__container {
		width: 100%;
		max-width: 400px;
		padding: var(--space-8);
		background-color: var(--color-bg);
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-lg);
	}

	.register-page__header {
		text-align: center;
		margin-bottom: var(--space-8);
	}

	.register-page__logo {
		margin: 0;
		font-size: var(--font-size-3xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-primary);
	}

	.register-page__subtitle {
		margin: var(--space-2) 0 0;
		font-size: var(--font-size-lg);
		color: var(--color-text-secondary);
	}

	.register-page__footer {
		margin-top: var(--space-6);
		text-align: center;
	}

	.register-page__text {
		margin: 0;
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.register-page__link {
		color: var(--color-primary);
		text-decoration: none;
		font-weight: var(--font-weight-medium);
	}

	.register-page__link:hover {
		text-decoration: underline;
	}

	.register-page__local-notice {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-2);
		margin-top: var(--space-6);
		padding-top: var(--space-4);
		border-top: 1px solid var(--color-border-light);
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.register-page__local-notice svg {
		color: var(--color-success);
	}
</style>
