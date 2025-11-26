/**
 * API Client
 * ragged WebUI v0.7.4
 *
 * Type-safe API client for backend communication with security features.
 */

import type {
	QueryRequest,
	QueryResponse,
	UploadResponse,
	Document,
	Collection,
	HealthResponse,
	ErrorResponse,
	QueryHistoryItem,
	PerformanceMetrics,
	StorageMetrics,
	SimilarityData,
	UserSettings
} from '$types';
import { withCsrfHeaders, rateLimiter, RATE_LIMITS } from '$utils';

const BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Custom API Error
 */
export class ApiError extends Error {
	constructor(
		message: string,
		public status: number,
		public code?: string
	) {
		super(message);
		this.name = 'ApiError';
	}
}

/**
 * Rate limit error
 */
export class RateLimitError extends Error {
	constructor(
		public retryAfter: number,
		message: string = 'Too many requests'
	) {
		super(message);
		this.name = 'RateLimitError';
	}
}

/**
 * Generic request function with error handling and security
 */
async function request<T>(
	endpoint: string,
	options: RequestInit = {},
	rateLimitKey?: string
): Promise<T> {
	// Check client-side rate limit
	if (rateLimitKey && rateLimiter.isLimited(rateLimitKey, RATE_LIMITS.api)) {
		const resetTime = rateLimiter.getResetTime(rateLimitKey);
		throw new RateLimitError(resetTime, 'Rate limit exceeded. Please wait and try again.');
	}

	const url = `${BASE_URL}${endpoint}`;

	// Add CSRF token for state-changing requests
	const method = options.method?.toUpperCase() || 'GET';
	const needsCsrf = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method);

	const response = await fetch(url, {
		...options,
		headers: needsCsrf
			? withCsrfHeaders({
					'Content-Type': 'application/json',
					...(options.headers as Record<string, string>)
				})
			: {
					'Content-Type': 'application/json',
					...options.headers
				},
		credentials: 'include' // Include cookies for session
	});

	// Handle rate limiting from server
	if (response.status === 429) {
		const retryAfter = parseInt(response.headers.get('Retry-After') || '60', 10) * 1000;
		throw new RateLimitError(retryAfter);
	}

	if (!response.ok) {
		let errorMessage = response.statusText;
		let errorCode: string | undefined;

		try {
			const errorData: ErrorResponse = await response.json();
			errorMessage = errorData.detail || errorMessage;
			errorCode = errorData.code;
		} catch {
			// Response body is not JSON
		}

		throw new ApiError(errorMessage, response.status, errorCode);
	}

	// Handle empty responses
	const contentType = response.headers.get('content-type');
	if (!contentType || !contentType.includes('application/json')) {
		return undefined as T;
	}

	return response.json();
}

/**
 * API client with typed methods
 */
export const api = {
	/**
	 * Health check endpoints
	 */
	health: {
		check: () => request<HealthResponse>('/api/health')
	},

	/**
	 * Query endpoints
	 */
	query: {
		submit: (req: QueryRequest) =>
			request<QueryResponse>('/api/query', {
				method: 'POST',
				body: JSON.stringify(req)
			})
	},

	/**
	 * Document endpoints
	 */
	documents: {
		list: () => request<Document[]>('/api/documents'),

		get: (id: string) => request<Document>(`/api/documents/${id}`),

		delete: (id: string) =>
			request<void>(`/api/documents/${id}`, {
				method: 'DELETE'
			}),

		upload: async (file: File): Promise<UploadResponse> => {
			const formData = new FormData();
			formData.append('file', file);

			const response = await fetch(`${BASE_URL}/api/upload`, {
				method: 'POST',
				body: formData,
				credentials: 'include'
			});

			if (!response.ok) {
				let errorMessage = 'Upload failed';
				try {
					const errorData = await response.json();
					errorMessage = errorData.detail || errorMessage;
				} catch {
					// Ignore JSON parse error
				}
				throw new ApiError(errorMessage, response.status);
			}

			return response.json();
		}
	},

	/**
	 * Collection endpoints
	 */
	collections: {
		list: () => request<Collection[]>('/api/collections'),

		get: (id: string) => request<Collection>(`/api/collections/${id}`),

		create: (data: { name: string; description?: string }) =>
			request<Collection>('/api/collections', {
				method: 'POST',
				body: JSON.stringify(data)
			}),

		update: (id: string, data: { name: string; description?: string }) =>
			request<Collection>(`/api/collections/${id}`, {
				method: 'PUT',
				body: JSON.stringify(data)
			}),

		delete: (id: string) =>
			request<void>(`/api/collections/${id}`, {
				method: 'DELETE'
			})
	},

	/**
	 * History endpoints
	 */
	history: {
		list: () => request<QueryHistoryItem[]>('/api/history'),

		get: (id: string) => request<QueryHistoryItem>(`/api/history/${id}`),

		delete: (id: string) =>
			request<void>(`/api/history/${id}`, {
				method: 'DELETE'
			}),

		clearAll: () =>
			request<void>('/api/history', {
				method: 'DELETE'
			})
	},

	/**
	 * Analytics endpoints
	 */
	analytics: {
		performance: (period?: string) =>
			request<PerformanceMetrics>(`/api/analytics/performance${period ? `?period=${period}` : ''}`),

		storage: () => request<StorageMetrics>('/api/analytics/storage'),

		similarity: (collectionId?: string) =>
			request<SimilarityData>(
				`/api/analytics/similarity${collectionId ? `?collection=${collectionId}` : ''}`
			)
	},

	/**
	 * Settings endpoints
	 */
	settings: {
		get: () => request<UserSettings>('/api/settings'),

		update: (settings: Partial<UserSettings>) =>
			request<UserSettings>('/api/settings', {
				method: 'PUT',
				body: JSON.stringify(settings)
			})
	},

	/**
	 * Metrics endpoints
	 */
	metrics: {
		get: async (): Promise<string> => {
			const response = await fetch(`${BASE_URL}/metrics`, {
				credentials: 'include'
			});

			if (!response.ok) {
				throw new ApiError('Failed to fetch metrics', response.status);
			}

			return response.text();
		}
	}
};

export default api;
