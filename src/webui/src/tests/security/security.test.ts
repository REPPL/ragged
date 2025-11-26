/**
 * Security Utility Tests
 * ragged WebUI v0.7.4 - SEC-002 to SEC-010
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
	safeHref,
	getCsrfToken,
	setCsrfToken,
	clearCsrfToken,
	withCsrfHeaders,
	parseJwtPayload,
	isTokenExpired,
	hasPermission,
	hasAllPermissions,
	hasAnyPermission,
	getPermissions,
	rateLimiter,
	RATE_LIMITS,
	secureStorage,
	generateSecureId,
	secureCompare
} from '$utils';

describe('SEC-002: XSS Prevention', () => {
	describe('safeHref', () => {
		it('should allow safe HTTP URLs', () => {
			expect(safeHref('https://example.com')).toBe('https://example.com');
			expect(safeHref('http://example.com')).toBe('http://example.com');
		});

		it('should block javascript: URLs', () => {
			expect(safeHref('javascript:alert(1)')).toBeNull();
			expect(safeHref('JAVASCRIPT:alert(1)')).toBeNull();
		});

		it('should block data: URLs', () => {
			expect(safeHref('data:text/html,<script>alert(1)</script>')).toBeNull();
		});

		it('should allow relative URLs', () => {
			expect(safeHref('/path/to/page')).toBe('/path/to/page');
			expect(safeHref('#anchor')).toBe('#anchor');
		});

		it('should allow mailto: URLs', () => {
			expect(safeHref('mailto:user@example.com')).toBe('mailto:user@example.com');
		});
	});
});

describe('SEC-003: CSRF Protection', () => {
	beforeEach(() => {
		// Clear session storage before each test
		if (typeof sessionStorage !== 'undefined') {
			sessionStorage.clear();
		}
	});

	describe('CSRF token management', () => {
		it('should set and get CSRF token', () => {
			setCsrfToken('test-token-123');
			expect(getCsrfToken()).toBe('test-token-123');
		});

		it('should clear CSRF token', () => {
			setCsrfToken('test-token-123');
			clearCsrfToken();
			expect(getCsrfToken()).toBeNull();
		});

		it('should add CSRF token to headers', () => {
			setCsrfToken('test-token-456');
			const headers = withCsrfHeaders({ 'Content-Type': 'application/json' });
			expect(headers['X-CSRF-Token']).toBe('test-token-456');
			expect(headers['Content-Type']).toBe('application/json');
		});

		it('should not add header when no token exists', () => {
			clearCsrfToken();
			const headers = withCsrfHeaders({ 'Content-Type': 'application/json' });
			expect(headers['X-CSRF-Token']).toBeUndefined();
		});
	});
});

describe('SEC-004: JWT Security', () => {
	describe('parseJwtPayload', () => {
		it('should parse valid JWT payload', () => {
			// Base64 encoded payload: {"sub":"1234567890","name":"Test User","exp":9999999999}
			const token = 'header.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IlRlc3QgVXNlciIsImV4cCI6OTk5OTk5OTk5OX0.signature';
			const payload = parseJwtPayload(token);

			expect(payload).not.toBeNull();
			expect(payload?.sub).toBe('1234567890');
			expect(payload?.name).toBe('Test User');
		});

		it('should return null for invalid tokens', () => {
			expect(parseJwtPayload('')).toBeNull();
			expect(parseJwtPayload('invalid')).toBeNull();
			expect(parseJwtPayload('only.two')).toBeNull();
		});
	});

	describe('isTokenExpired', () => {
		it('should detect expired tokens', () => {
			// Expired token (exp in past)
			const expiredPayload = btoa(JSON.stringify({ exp: 1 }));
			const expiredToken = `header.${expiredPayload}.signature`;
			expect(isTokenExpired(expiredToken)).toBe(true);
		});

		it('should detect valid tokens', () => {
			// Valid token (exp far in future)
			const validPayload = btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 3600 }));
			const validToken = `header.${validPayload}.signature`;
			expect(isTokenExpired(validToken)).toBe(false);
		});

		it('should treat tokens without exp as expired', () => {
			const noExpPayload = btoa(JSON.stringify({ sub: '123' }));
			const noExpToken = `header.${noExpPayload}.signature`;
			expect(isTokenExpired(noExpToken)).toBe(true);
		});
	});
});

describe('SEC-005: Authorization Enforcement', () => {
	describe('hasPermission', () => {
		it('should return true for admin permissions', () => {
			expect(hasPermission('admin', 'view:documents')).toBe(true);
			expect(hasPermission('admin', 'admin:users')).toBe(true);
		});

		it('should return false for insufficient permissions', () => {
			expect(hasPermission('viewer', 'upload:documents')).toBe(false);
			expect(hasPermission('guest', 'view:analytics')).toBe(false);
		});

		it('should handle null/undefined roles', () => {
			expect(hasPermission(null, 'view:documents')).toBe(false);
			expect(hasPermission(undefined, 'view:documents')).toBe(false);
		});
	});

	describe('hasAllPermissions', () => {
		it('should check all permissions', () => {
			expect(hasAllPermissions('admin', ['view:documents', 'upload:documents'])).toBe(true);
			expect(hasAllPermissions('viewer', ['view:documents', 'upload:documents'])).toBe(false);
		});
	});

	describe('hasAnyPermission', () => {
		it('should check any permission', () => {
			expect(hasAnyPermission('viewer', ['view:documents', 'upload:documents'])).toBe(true);
			expect(hasAnyPermission('guest', ['upload:documents', 'delete:documents'])).toBe(false);
		});
	});

	describe('getPermissions', () => {
		it('should return all permissions for a role', () => {
			const adminPerms = getPermissions('admin');
			expect(adminPerms).toContain('admin:users');
			expect(adminPerms).toContain('view:documents');

			const viewerPerms = getPermissions('viewer');
			expect(viewerPerms).toContain('view:documents');
			expect(viewerPerms).not.toContain('admin:users');
		});
	});
});

describe('SEC-007: Rate Limiting', () => {
	beforeEach(() => {
		rateLimiter.reset('test-key');
	});

	describe('rateLimiter', () => {
		it('should allow requests under limit', () => {
			const config = { maxRequests: 5, windowMs: 60000 };

			for (let i = 0; i < 5; i++) {
				expect(rateLimiter.isLimited('test-key', config)).toBe(false);
			}
		});

		it('should block requests over limit', () => {
			const config = { maxRequests: 3, windowMs: 60000 };

			for (let i = 0; i < 3; i++) {
				rateLimiter.isLimited('test-key', config);
			}

			expect(rateLimiter.isLimited('test-key', config)).toBe(true);
		});

		it('should track remaining requests', () => {
			const config = { maxRequests: 5, windowMs: 60000 };

			rateLimiter.isLimited('test-key', config);
			rateLimiter.isLimited('test-key', config);

			expect(rateLimiter.getRemaining('test-key', config)).toBe(3);
		});

		it('should reset after window expires', () => {
			vi.useFakeTimers();

			const config = { maxRequests: 2, windowMs: 1000 };

			rateLimiter.isLimited('test-key', config);
			rateLimiter.isLimited('test-key', config);
			expect(rateLimiter.isLimited('test-key', config)).toBe(true);

			vi.advanceTimersByTime(1001);
			expect(rateLimiter.isLimited('test-key', config)).toBe(false);

			vi.useRealTimers();
		});
	});

	describe('RATE_LIMITS configurations', () => {
		it('should have sensible defaults', () => {
			expect(RATE_LIMITS.query.maxRequests).toBeGreaterThan(0);
			expect(RATE_LIMITS.upload.maxRequests).toBeGreaterThan(0);
			expect(RATE_LIMITS.login.maxRequests).toBeGreaterThan(0);
		});
	});
});

describe('SEC-010: Secure Storage', () => {
	beforeEach(() => {
		if (typeof localStorage !== 'undefined') {
			localStorage.clear();
		}
		if (typeof sessionStorage !== 'undefined') {
			sessionStorage.clear();
		}
	});

	describe('secureStorage', () => {
		it('should store and retrieve preferences', () => {
			secureStorage.setPreference('theme', 'dark');
			expect(secureStorage.getPreference('theme')).toBe('dark');
		});

		it('should store and retrieve session data', () => {
			secureStorage.setSession('auth', 'token-123');
			expect(secureStorage.getSession('auth')).toBe('token-123');
		});

		it('should clear session data', () => {
			secureStorage.setSession('auth', 'token-123');
			secureStorage.setPreference('theme', 'dark');

			secureStorage.clearSession();

			expect(secureStorage.getSession('auth')).toBeNull();
			expect(secureStorage.getPreference('theme')).toBe('dark');
		});

		it('should clear all data', () => {
			secureStorage.setSession('auth', 'token-123');
			secureStorage.setPreference('theme', 'dark');

			secureStorage.clearAll();

			expect(secureStorage.getSession('auth')).toBeNull();
			expect(secureStorage.getPreference('theme')).toBeNull();
		});
	});
});

describe('Security Utilities', () => {
	describe('generateSecureId', () => {
		it('should generate unique IDs', () => {
			const id1 = generateSecureId();
			const id2 = generateSecureId();

			expect(id1).not.toBe(id2);
		});

		it('should generate IDs of correct length', () => {
			const id = generateSecureId(16);
			expect(id.length).toBeGreaterThanOrEqual(16);
		});
	});

	describe('secureCompare', () => {
		it('should return true for matching strings', () => {
			expect(secureCompare('abc123', 'abc123')).toBe(true);
		});

		it('should return false for non-matching strings', () => {
			expect(secureCompare('abc123', 'abc124')).toBe(false);
			expect(secureCompare('abc123', 'abc12')).toBe(false);
		});

		it('should return false for different length strings', () => {
			expect(secureCompare('short', 'longer')).toBe(false);
		});
	});
});
