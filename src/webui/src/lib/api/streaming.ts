/**
 * Streaming API Client
 * ragged WebUI v0.7.3
 *
 * Server-Sent Events (SSE) streaming for query responses
 */

import type { QueryRequest, Source } from '$types';

const BASE_URL = import.meta.env.VITE_API_URL || '';

export interface StreamCallbacks {
	onStatus?: (message: string) => void;
	onRetrieved?: (count: number, method: string) => void;
	onToken?: (token: string) => void;
	onSources?: (sources: Source[]) => void;
	onComplete?: (totalTime: number) => void;
	onError?: (error: string) => void;
}

/**
 * Stream a query response using Server-Sent Events
 *
 * @param request - Query request parameters
 * @param callbacks - Event callbacks for different SSE events
 * @returns Abort function to cancel the stream
 */
export function streamQuery(request: QueryRequest, callbacks: StreamCallbacks): () => void {
	const controller = new AbortController();

	(async () => {
		try {
			const response = await fetch(`${BASE_URL}/api/query`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Accept: 'text/event-stream'
				},
				body: JSON.stringify({ ...request, stream: true }),
				signal: controller.signal,
				credentials: 'include'
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({}));
				callbacks.onError?.(errorData.detail || `Query failed: ${response.statusText}`);
				return;
			}

			if (!response.body) {
				callbacks.onError?.('No response body');
				return;
			}

			const reader = response.body.getReader();
			const decoder = new TextDecoder();
			let buffer = '';
			let currentEvent: string | null = null;

			while (true) {
				const { done, value } = await reader.read();

				if (done) {
					break;
				}

				buffer += decoder.decode(value, { stream: true });
				const lines = buffer.split('\n');
				buffer = lines.pop() || '';

				for (const line of lines) {
					if (line.startsWith('event: ')) {
						currentEvent = line.slice(7).trim();
					} else if (line.startsWith('data: ') && currentEvent) {
						try {
							const data = JSON.parse(line.slice(6));
							handleEvent(currentEvent, data, callbacks);
						} catch {
							// Invalid JSON, skip
						}
						currentEvent = null;
					}
				}
			}
		} catch (error) {
			if (error instanceof Error && error.name !== 'AbortError') {
				callbacks.onError?.(error.message);
			}
		}
	})();

	return () => controller.abort();
}

/**
 * Handle individual SSE events
 */
function handleEvent(event: string, data: unknown, callbacks: StreamCallbacks): void {
	switch (event) {
		case 'status':
			if (isStatusData(data)) {
				callbacks.onStatus?.(data.message);
			}
			break;

		case 'retrieved':
			if (isRetrievedData(data)) {
				callbacks.onRetrieved?.(data.count, data.method);
			}
			break;

		case 'token':
			if (isTokenData(data)) {
				callbacks.onToken?.(data.token);
			}
			break;

		case 'sources':
			if (Array.isArray(data)) {
				callbacks.onSources?.(data as Source[]);
			}
			break;

		case 'complete':
			if (isCompleteData(data)) {
				callbacks.onComplete?.(data.total_time);
			}
			break;

		case 'error':
			if (isErrorData(data)) {
				callbacks.onError?.(data.error);
			}
			break;
	}
}

// Type guards
function isStatusData(data: unknown): data is { message: string } {
	return typeof data === 'object' && data !== null && 'message' in data;
}

function isRetrievedData(data: unknown): data is { count: number; method: string } {
	return typeof data === 'object' && data !== null && 'count' in data && 'method' in data;
}

function isTokenData(data: unknown): data is { token: string } {
	return typeof data === 'object' && data !== null && 'token' in data;
}

function isCompleteData(data: unknown): data is { total_time: number } {
	return typeof data === 'object' && data !== null && 'total_time' in data;
}

function isErrorData(data: unknown): data is { error: string } {
	return typeof data === 'object' && data !== null && 'error' in data;
}
