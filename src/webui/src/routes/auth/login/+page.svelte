<!--
  Login Page
  ragged WebUI v0.7.3

  User login interface
-->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { auth, addToast } from '$stores';
	import { AuthForm } from '$lib/components/auth';

	let loading = false;
	let error: string | null = null;

	/**
	 * Validates that a redirect URL is safe (relative path only)
	 * Prevents open redirect attacks
	 */
	function isValidRedirect(url: string | null): boolean {
		if (!url) return false;
		// Only allow relative paths starting with /
		// Reject protocol-relative URLs (//) and absolute URLs
		return url.startsWith('/') && !url.startsWith('//') && !url.includes('://');
	}

	// Get redirect URL from query params with validation
	$: redirectParam = $page.url.searchParams.get('redirect');
	$: redirectTo = isValidRedirect(redirectParam) ? redirectParam! : '/';

	async function handleSubmit(event: CustomEvent<{ email: string; password: string }>) {
		loading = true;
		error = null;

		try {
			// In a real app, this would call the API
			const response = await fetch('/api/auth/login', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(event.detail),
				credentials: 'include'
			});

			if (!response.ok) {
				const data = await response.json();
				throw new Error(data.detail || 'Login failed');
			}

			const userData = await response.json();
			auth.setUser(userData);

			addToast({
				type: 'success',
				title: 'Welcome back!',
				message: `Signed in as ${userData.email}`
			});

			goto(redirectTo);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Login failed';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Sign in - ragged</title>
</svelte:head>

<div class="login-page">
	<div class="login-page__container">
		<div class="login-page__header">
			<h1 class="login-page__logo">ragged</h1>
			<p class="login-page__subtitle">Sign in to your account</p>
		</div>

		<div class="login-page__form">
			<AuthForm
				mode="login"
				{loading}
				{error}
				on:submit={handleSubmit}
			/>
		</div>

		<div class="login-page__footer">
			<p class="login-page__text">
				Don't have an account?
				<a href="/auth/register" class="login-page__link">Create one</a>
			</p>
		</div>

		<div class="login-page__local-notice">
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
				<path d="M7 11V7a5 5 0 0110 0v4" />
			</svg>
			<span>All data stays local on your machine</span>
		</div>
	</div>
</div>

<style>
	.login-page {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 100vh;
		padding: var(--space-4);
		background-color: var(--color-bg-secondary);
	}

	.login-page__container {
		width: 100%;
		max-width: 400px;
		padding: var(--space-8);
		background-color: var(--color-bg);
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-lg);
	}

	.login-page__header {
		text-align: center;
		margin-bottom: var(--space-8);
	}

	.login-page__logo {
		margin: 0;
		font-size: var(--font-size-3xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-primary);
	}

	.login-page__subtitle {
		margin: var(--space-2) 0 0;
		font-size: var(--font-size-lg);
		color: var(--color-text-secondary);
	}

	.login-page__footer {
		margin-top: var(--space-6);
		text-align: center;
	}

	.login-page__text {
		margin: 0;
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.login-page__link {
		color: var(--color-primary);
		text-decoration: none;
		font-weight: var(--font-weight-medium);
	}

	.login-page__link:hover {
		text-decoration: underline;
	}

	.login-page__local-notice {
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

	.login-page__local-notice svg {
		color: var(--color-success);
	}
</style>
