/**
 * Server Hooks
 * ragged WebUI v0.7.4 - SEC-008
 *
 * Server-side hooks for security headers, CSRF protection, and request handling.
 */
import type { Handle, HandleServerError } from '@sveltejs/kit';
import { sequence } from '@sveltejs/kit/hooks';

/**
 * Security headers hook.
 * Adds recommended security headers to all responses.
 */
const securityHeaders: Handle = async ({ event, resolve }) => {
	const response = await resolve(event);

	// Security headers
	response.headers.set('X-Content-Type-Options', 'nosniff');
	response.headers.set('X-Frame-Options', 'DENY');
	response.headers.set('X-XSS-Protection', '1; mode=block');
	response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
	response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');

	// HSTS - only in production
	if (event.url.protocol === 'https:') {
		response.headers.set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
	}

	return response;
};

/**
 * CSRF protection hook.
 * Validates CSRF tokens on state-changing requests.
 */
const csrfProtection: Handle = async ({ event, resolve }) => {
	const method = event.request.method;

	// Only check state-changing methods
	if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
		// Skip CSRF check for API routes (they use different auth)
		if (!event.url.pathname.startsWith('/api/')) {
			const csrfToken = event.request.headers.get('X-CSRF-Token');
			const sessionToken = event.cookies.get('csrf_token');

			// If CSRF protection is enabled and tokens don't match
			if (sessionToken && csrfToken !== sessionToken) {
				return new Response('Invalid CSRF token', { status: 403 });
			}
		}
	}

	return resolve(event);
};

/**
 * Request logging hook (development only).
 */
const requestLogging: Handle = async ({ event, resolve }) => {
	const start = Date.now();
	const response = await resolve(event);
	const duration = Date.now() - start;

	// Only log in development
	if (import.meta.env.DEV) {
		console.log(`${event.request.method} ${event.url.pathname} - ${response.status} (${duration}ms)`);
	}

	return response;
};

/**
 * Rate limiting hook.
 * Basic IP-based rate limiting for auth endpoints.
 */
const rateLimits: Map<string, { count: number; resetTime: number }> = new Map();

const rateLimiting: Handle = async ({ event, resolve }) => {
	const path = event.url.pathname;

	// Only rate limit auth endpoints
	if (path.startsWith('/auth/')) {
		const clientIP = event.getClientAddress();
		const key = `${clientIP}:${path}`;
		const now = Date.now();
		const windowMs = 5 * 60 * 1000; // 5 minutes
		const maxRequests = 10; // 10 requests per 5 minutes

		const state = rateLimits.get(key);

		if (state && now < state.resetTime) {
			if (state.count >= maxRequests) {
				return new Response('Too many requests. Please try again later.', {
					status: 429,
					headers: {
						'Retry-After': String(Math.ceil((state.resetTime - now) / 1000))
					}
				});
			}
			state.count++;
		} else {
			rateLimits.set(key, { count: 1, resetTime: now + windowMs });
		}

		// Clean up old entries periodically
		if (Math.random() < 0.01) {
			for (const [k, v] of rateLimits.entries()) {
				if (now >= v.resetTime) {
					rateLimits.delete(k);
				}
			}
		}
	}

	return resolve(event);
};

/**
 * Combined handle hook.
 */
export const handle: Handle = sequence(
	requestLogging,
	rateLimiting,
	csrfProtection,
	securityHeaders
);

/**
 * Server error handler.
 * Sanitises error messages to prevent information leakage.
 */
export const handleError: HandleServerError = async ({ error, event, status, message }) => {
	// Log the full error server-side
	console.error(`[${event.request.method}] ${event.url.pathname}:`, error);

	// Return sanitised error to client
	return {
		message: status === 404 ? 'Not found' : 'An error occurred',
		code: status.toString()
	};
};
