/**
 * Security Utilities
 * ragged WebUI v0.7.4 - SEC-002 to SEC-010
 *
 * Comprehensive security utilities for the WebUI including:
 * - XSS prevention
 * - CSRF protection
 * - Rate limiting
 * - Secure storage
 * - Authorization helpers
 */

// ============================================
// SEC-002: XSS PREVENTION
// ============================================

/**
 * Create a safe href attribute value.
 * Prevents javascript: and data: URLs.
 */
export function safeHref(url: string): string | null {
	if (!url) return null;

	const trimmed = url.trim().toLowerCase();

	// Block dangerous protocols
	const dangerousProtocols = ['javascript:', 'data:', 'vbscript:', 'file:'];
	for (const protocol of dangerousProtocols) {
		if (trimmed.startsWith(protocol)) {
			console.warn(`Blocked dangerous URL protocol: ${protocol}`);
			return null;
		}
	}

	// Allow relative URLs and safe protocols
	if (
		trimmed.startsWith('/') ||
		trimmed.startsWith('#') ||
		trimmed.startsWith('http://') ||
		trimmed.startsWith('https://') ||
		trimmed.startsWith('mailto:')
	) {
		return url;
	}

	// Default: treat as relative URL
	return url;
}

/**
 * Safely set innerHTML with DOMPurify (must import DOMPurify separately).
 * This is a marker function for code review - actual sanitisation uses DOMPurify.
 */
export function markAsSanitized(content: string): string {
	// This function serves as documentation that content has been sanitised
	// Actual sanitisation should be done with DOMPurify before calling this
	return content;
}

// ============================================
// SEC-003: CSRF PROTECTION
// ============================================

/**
 * CSRF token storage key.
 */
const CSRF_TOKEN_KEY = 'ragged_csrf_token';

/**
 * Get the current CSRF token from meta tag or storage.
 */
export function getCsrfToken(): string | null {
	// First try to get from meta tag (set by server)
	if (typeof document !== 'undefined') {
		const meta = document.querySelector('meta[name="csrf-token"]');
		if (meta) {
			return meta.getAttribute('content');
		}
	}

	// Fall back to session storage
	if (typeof sessionStorage !== 'undefined') {
		return sessionStorage.getItem(CSRF_TOKEN_KEY);
	}

	return null;
}

/**
 * Set the CSRF token (typically from server response).
 */
export function setCsrfToken(token: string): void {
	if (typeof sessionStorage !== 'undefined') {
		sessionStorage.setItem(CSRF_TOKEN_KEY, token);
	}
}

/**
 * Clear the CSRF token (on logout).
 */
export function clearCsrfToken(): void {
	if (typeof sessionStorage !== 'undefined') {
		sessionStorage.removeItem(CSRF_TOKEN_KEY);
	}
}

/**
 * Add CSRF token to request headers.
 */
export function withCsrfHeaders(headers: Record<string, string> = {}): Record<string, string> {
	const token = getCsrfToken();
	if (token) {
		return {
			...headers,
			'X-CSRF-Token': token
		};
	}
	return headers;
}

// ============================================
// SEC-004: JWT & SESSION SECURITY
// ============================================

/**
 * Parse a JWT token without validation (for client-side checks only).
 * Never trust this for security decisions - server must validate.
 */
export function parseJwtPayload(token: string): Record<string, unknown> | null {
	try {
		const parts = token.split('.');
		if (parts.length !== 3) return null;

		const payload = parts[1];
		const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
		return JSON.parse(decoded);
	} catch {
		return null;
	}
}

/**
 * Check if a JWT token appears to be expired (client-side check only).
 */
export function isTokenExpired(token: string): boolean {
	const payload = parseJwtPayload(token);
	if (!payload || typeof payload.exp !== 'number') {
		return true;
	}

	// Add 30 second buffer for clock skew
	const now = Math.floor(Date.now() / 1000);
	return payload.exp < now - 30;
}

/**
 * Session timeout tracker.
 */
class SessionManager {
	private timeoutId: ReturnType<typeof setTimeout> | null = null;
	private warningId: ReturnType<typeof setTimeout> | null = null;
	private lastActivity: number = Date.now();
	private readonly sessionTimeout: number;
	private readonly warningBefore: number;
	private onTimeout?: () => void;
	private onWarning?: () => void;

	constructor(sessionTimeoutMs: number = 30 * 60 * 1000, warningBeforeMs: number = 5 * 60 * 1000) {
		this.sessionTimeout = sessionTimeoutMs;
		this.warningBefore = warningBeforeMs;
	}

	/**
	 * Start tracking session activity.
	 */
	start(callbacks: { onTimeout?: () => void; onWarning?: () => void } = {}): void {
		this.onTimeout = callbacks.onTimeout;
		this.onWarning = callbacks.onWarning;
		this.resetTimers();

		// Track user activity
		if (typeof window !== 'undefined') {
			const events = ['mousedown', 'keydown', 'touchstart', 'scroll'];
			events.forEach((event) => {
				window.addEventListener(event, () => this.onActivity(), { passive: true });
			});
		}
	}

	/**
	 * Stop tracking session.
	 */
	stop(): void {
		if (this.timeoutId) {
			clearTimeout(this.timeoutId);
			this.timeoutId = null;
		}
		if (this.warningId) {
			clearTimeout(this.warningId);
			this.warningId = null;
		}
	}

	/**
	 * Record user activity and reset timers.
	 */
	private onActivity(): void {
		const now = Date.now();
		// Throttle activity updates to every 30 seconds
		if (now - this.lastActivity > 30000) {
			this.lastActivity = now;
			this.resetTimers();
		}
	}

	/**
	 * Reset the session timers.
	 */
	private resetTimers(): void {
		this.stop();

		// Set warning timer
		const warningTime = this.sessionTimeout - this.warningBefore;
		if (warningTime > 0 && this.onWarning) {
			this.warningId = setTimeout(() => {
				this.onWarning?.();
			}, warningTime);
		}

		// Set timeout timer
		if (this.onTimeout) {
			this.timeoutId = setTimeout(() => {
				this.onTimeout?.();
			}, this.sessionTimeout);
		}
	}

	/**
	 * Extend the session (e.g., after user clicks "Stay logged in").
	 */
	extend(): void {
		this.lastActivity = Date.now();
		this.resetTimers();
	}
}

export const sessionManager = new SessionManager();

// ============================================
// SEC-005: AUTHORIZATION HELPERS
// ============================================

export type Permission =
	| 'view:documents'
	| 'upload:documents'
	| 'delete:documents'
	| 'manage:collections'
	| 'view:analytics'
	| 'manage:settings'
	| 'admin:users';

export type Role = 'admin' | 'editor' | 'viewer' | 'guest';

/**
 * Role-permission mapping.
 */
const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
	admin: [
		'view:documents',
		'upload:documents',
		'delete:documents',
		'manage:collections',
		'view:analytics',
		'manage:settings',
		'admin:users'
	],
	editor: [
		'view:documents',
		'upload:documents',
		'delete:documents',
		'manage:collections',
		'view:analytics'
	],
	viewer: ['view:documents', 'view:analytics'],
	guest: ['view:documents']
};

/**
 * Check if a role has a specific permission.
 */
export function hasPermission(role: Role | undefined | null, permission: Permission): boolean {
	if (!role) return false;
	const permissions = ROLE_PERMISSIONS[role];
	return permissions?.includes(permission) ?? false;
}

/**
 * Check if a role has all specified permissions.
 */
export function hasAllPermissions(role: Role | undefined | null, permissions: Permission[]): boolean {
	return permissions.every((p) => hasPermission(role, p));
}

/**
 * Check if a role has any of the specified permissions.
 */
export function hasAnyPermission(role: Role | undefined | null, permissions: Permission[]): boolean {
	return permissions.some((p) => hasPermission(role, p));
}

/**
 * Get all permissions for a role.
 */
export function getPermissions(role: Role): Permission[] {
	return ROLE_PERMISSIONS[role] ?? [];
}

// ============================================
// SEC-007: RATE LIMITING
// ============================================

interface RateLimitConfig {
	maxRequests: number;
	windowMs: number;
}

interface RateLimitState {
	count: number;
	resetTime: number;
}

/**
 * Client-side rate limiter.
 * Note: This is a UX improvement only - actual rate limiting must be server-side.
 */
class RateLimiter {
	private limits: Map<string, RateLimitState> = new Map();

	/**
	 * Check if an action is rate limited.
	 */
	isLimited(key: string, config: RateLimitConfig): boolean {
		const now = Date.now();
		const state = this.limits.get(key);

		if (!state || now >= state.resetTime) {
			// Start new window
			this.limits.set(key, {
				count: 1,
				resetTime: now + config.windowMs
			});
			return false;
		}

		if (state.count >= config.maxRequests) {
			return true;
		}

		state.count++;
		return false;
	}

	/**
	 * Get remaining requests in current window.
	 */
	getRemaining(key: string, config: RateLimitConfig): number {
		const state = this.limits.get(key);
		if (!state || Date.now() >= state.resetTime) {
			return config.maxRequests;
		}
		return Math.max(0, config.maxRequests - state.count);
	}

	/**
	 * Get time until rate limit resets (ms).
	 */
	getResetTime(key: string): number {
		const state = this.limits.get(key);
		if (!state) return 0;
		return Math.max(0, state.resetTime - Date.now());
	}

	/**
	 * Reset rate limit for a key.
	 */
	reset(key: string): void {
		this.limits.delete(key);
	}
}

export const rateLimiter = new RateLimiter();

/**
 * Default rate limit configurations.
 */
export const RATE_LIMITS = {
	query: { maxRequests: 10, windowMs: 60000 }, // 10 queries per minute
	upload: { maxRequests: 5, windowMs: 60000 }, // 5 uploads per minute
	login: { maxRequests: 5, windowMs: 300000 }, // 5 attempts per 5 minutes
	api: { maxRequests: 100, windowMs: 60000 } // 100 API calls per minute
} as const;

// ============================================
// SEC-010: SECURE STORAGE
// ============================================

/**
 * Secure storage wrapper that handles sensitive data appropriately.
 * Uses sessionStorage for sensitive data (cleared on tab close).
 */
export const secureStorage = {
	/**
	 * Store a non-sensitive preference (persists across sessions).
	 */
	setPreference(key: string, value: string): void {
		if (typeof localStorage !== 'undefined') {
			localStorage.setItem(`ragged_pref_${key}`, value);
		}
	},

	/**
	 * Get a non-sensitive preference.
	 */
	getPreference(key: string): string | null {
		if (typeof localStorage !== 'undefined') {
			return localStorage.getItem(`ragged_pref_${key}`);
		}
		return null;
	},

	/**
	 * Store sensitive session data (cleared on tab close).
	 */
	setSession(key: string, value: string): void {
		if (typeof sessionStorage !== 'undefined') {
			sessionStorage.setItem(`ragged_sess_${key}`, value);
		}
	},

	/**
	 * Get sensitive session data.
	 */
	getSession(key: string): string | null {
		if (typeof sessionStorage !== 'undefined') {
			return sessionStorage.getItem(`ragged_sess_${key}`);
		}
		return null;
	},

	/**
	 * Clear all ragged session data.
	 */
	clearSession(): void {
		if (typeof sessionStorage !== 'undefined') {
			const keysToRemove: string[] = [];
			for (let i = 0; i < sessionStorage.length; i++) {
				const key = sessionStorage.key(i);
				if (key?.startsWith('ragged_')) {
					keysToRemove.push(key);
				}
			}
			keysToRemove.forEach((key) => sessionStorage.removeItem(key));
		}
	},

	/**
	 * Clear all ragged data (preferences and session).
	 */
	clearAll(): void {
		this.clearSession();
		if (typeof localStorage !== 'undefined') {
			const keysToRemove: string[] = [];
			for (let i = 0; i < localStorage.length; i++) {
				const key = localStorage.key(i);
				if (key?.startsWith('ragged_')) {
					keysToRemove.push(key);
				}
			}
			keysToRemove.forEach((key) => localStorage.removeItem(key));
		}
	}
};

// ============================================
// SECURITY HEADERS (for reference)
// ============================================

/**
 * Recommended security headers for server configuration.
 * These should be set server-side (in SvelteKit hooks or reverse proxy).
 */
export const RECOMMENDED_SECURITY_HEADERS = {
	'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
	'X-Content-Type-Options': 'nosniff',
	'X-Frame-Options': 'DENY',
	'X-XSS-Protection': '1; mode=block',
	'Referrer-Policy': 'strict-origin-when-cross-origin',
	'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
};

// ============================================
// UTILITY EXPORTS
// ============================================

/**
 * Generate a cryptographically secure random string.
 */
export function generateSecureId(length: number = 32): string {
	if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
		const array = new Uint8Array(length);
		crypto.getRandomValues(array);
		return Array.from(array, (byte) => byte.toString(16).padStart(2, '0')).join('');
	}
	// Fallback for environments without crypto
	return Math.random().toString(36).substring(2, length + 2);
}

/**
 * Constant-time string comparison to prevent timing attacks.
 */
export function secureCompare(a: string, b: string): boolean {
	if (a.length !== b.length) return false;

	let result = 0;
	for (let i = 0; i < a.length; i++) {
		result |= a.charCodeAt(i) ^ b.charCodeAt(i);
	}
	return result === 0;
}
