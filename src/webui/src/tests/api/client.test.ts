/**
 * API Client Tests
 * ragged WebUI v0.7.3
 */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { api, ApiError } from '$lib/api/client';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('API Client', () => {
	beforeEach(() => {
		mockFetch.mockReset();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	describe('health.check', () => {
		it('returns health data on success', async () => {
			const healthData = {
				status: 'healthy',
				version: '0.7.3',
				services: { vectorstore: 'ok', llm: 'ok' }
			};

			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(healthData),
				headers: new Headers({ 'content-type': 'application/json' })
			});

			const result = await api.health.check();
			expect(result).toEqual(healthData);
			expect(mockFetch).toHaveBeenCalledWith(
				'/api/health',
				expect.objectContaining({
					headers: expect.objectContaining({
						'Content-Type': 'application/json'
					})
				})
			);
		});

		it('throws ApiError on failure', async () => {
			mockFetch.mockResolvedValueOnce({
				ok: false,
				status: 503,
				statusText: 'Service Unavailable',
				json: () => Promise.resolve({ detail: 'Service is down' })
			});

			await expect(api.health.check()).rejects.toThrow(ApiError);
			await expect(api.health.check()).rejects.toThrow('Service is down');
		});
	});

	describe('documents.list', () => {
		it('returns document list on success', async () => {
			const documents = [
				{ id: '1', filename: 'test.pdf', size: 1024 },
				{ id: '2', filename: 'test2.md', size: 512 }
			];

			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(documents),
				headers: new Headers({ 'content-type': 'application/json' })
			});

			const result = await api.documents.list();
			expect(result).toEqual(documents);
		});
	});

	describe('documents.upload', () => {
		it('uploads file successfully', async () => {
			const uploadResponse = {
				filename: 'test.pdf',
				size: 1024,
				status: 'success',
				message: 'File uploaded'
			};

			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(uploadResponse)
			});

			const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
			const result = await api.documents.upload(file);

			expect(result).toEqual(uploadResponse);
			expect(mockFetch).toHaveBeenCalledWith(
				'/api/upload',
				expect.objectContaining({
					method: 'POST',
					body: expect.any(FormData)
				})
			);
		});

		it('throws ApiError on upload failure', async () => {
			mockFetch.mockResolvedValueOnce({
				ok: false,
				status: 413,
				json: () => Promise.resolve({ detail: 'File too large' })
			});

			const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
			await expect(api.documents.upload(file)).rejects.toThrow(ApiError);
		});
	});

	describe('collections.create', () => {
		it('creates collection successfully', async () => {
			const collection = {
				id: '1',
				name: 'test-collection',
				description: 'A test collection',
				document_count: 0,
				created_at: new Date().toISOString()
			};

			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(collection),
				headers: new Headers({ 'content-type': 'application/json' })
			});

			const result = await api.collections.create({
				name: 'test-collection',
				description: 'A test collection'
			});

			expect(result).toEqual(collection);
			expect(mockFetch).toHaveBeenCalledWith(
				'/api/collections',
				expect.objectContaining({
					method: 'POST',
					body: JSON.stringify({
						name: 'test-collection',
						description: 'A test collection'
					})
				})
			);
		});
	});

	describe('query.submit', () => {
		it('submits query successfully', async () => {
			const queryResponse = {
				answer: 'This is the answer',
				sources: [{ id: '1', filename: 'test.pdf', score: 0.95 }],
				retrieval_method: 'hybrid',
				total_time: 1.5
			};

			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(queryResponse),
				headers: new Headers({ 'content-type': 'application/json' })
			});

			const result = await api.query.submit({
				query: 'What is the answer?',
				top_k: 5
			});

			expect(result).toEqual(queryResponse);
			expect(mockFetch).toHaveBeenCalledWith(
				'/api/query',
				expect.objectContaining({
					method: 'POST',
					body: expect.stringContaining('What is the answer?')
				})
			);
		});
	});
});
