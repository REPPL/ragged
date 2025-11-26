<!--
	Authorization Guard Component
	ragged WebUI v0.7.4 - SEC-005

	Conditionally renders content based on user permissions.
-->
<script lang="ts">
	import { auth } from '$stores';
	import { hasPermission, hasAllPermissions, hasAnyPermission } from '$utils';
	import type { Permission, Role } from '$utils';

	/**
	 * Single permission required to view content.
	 */
	export let permission: Permission | undefined = undefined;

	/**
	 * Multiple permissions - all required to view content.
	 */
	export let allPermissions: Permission[] | undefined = undefined;

	/**
	 * Multiple permissions - any one grants access.
	 */
	export let anyPermission: Permission[] | undefined = undefined;

	/**
	 * Specific roles allowed.
	 */
	export let roles: Role[] | undefined = undefined;

	/**
	 * Whether to show a fallback when access is denied.
	 */
	export let showFallback: boolean = false;

	/**
	 * Custom fallback message.
	 */
	export let fallbackMessage: string = 'You do not have permission to view this content.';

	// Compute access
	$: userRole = $auth.user?.role as Role | undefined;

	$: hasAccess = (() => {
		// Not authenticated
		if (!$auth.isAuthenticated || !userRole) {
			return false;
		}

		// Check roles if specified
		if (roles && roles.length > 0) {
			if (!roles.includes(userRole)) {
				return false;
			}
		}

		// Check single permission
		if (permission) {
			if (!hasPermission(userRole, permission)) {
				return false;
			}
		}

		// Check all permissions
		if (allPermissions && allPermissions.length > 0) {
			if (!hasAllPermissions(userRole, allPermissions)) {
				return false;
			}
		}

		// Check any permission
		if (anyPermission && anyPermission.length > 0) {
			if (!hasAnyPermission(userRole, anyPermission)) {
				return false;
			}
		}

		return true;
	})();
</script>

{#if hasAccess}
	<slot />
{:else if showFallback}
	<slot name="fallback">
		<div class="auth-guard__fallback" role="alert">
			<svg
				class="auth-guard__icon"
				width="24"
				height="24"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
			>
				<circle cx="12" cy="12" r="10" />
				<line x1="12" y1="8" x2="12" y2="12" />
				<line x1="12" y1="16" x2="12.01" y2="16" />
			</svg>
			<p class="auth-guard__message">{fallbackMessage}</p>
		</div>
	</slot>
{/if}

<style>
	.auth-guard__fallback {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--space-8);
		text-align: center;
		color: var(--color-text-muted);
	}

	.auth-guard__icon {
		margin-bottom: var(--space-4);
		color: var(--color-warning);
	}

	.auth-guard__message {
		margin: 0;
		font-size: var(--font-size-sm);
	}
</style>
