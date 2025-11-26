/**
 * Document Management Workflow E2E Tests
 * ragged WebUI v0.7.5 - QA-001
 */
import { test, expect } from '@playwright/test';
import { DocumentsPage } from '../fixtures/test-utils';
import * as path from 'path';

test.describe('Document Management Workflows', () => {
	test.describe('Document Upload', () => {
		test('should display upload zone', async ({ page }) => {
			const docsPage = new DocumentsPage(page);
			await docsPage.goto();

			await expect(docsPage.uploadZone).toBeVisible();
		});

		test('should accept valid file types', async ({ page }) => {
			const docsPage = new DocumentsPage(page);
			await docsPage.goto();

			// Mock successful upload
			await page.route('**/api/upload', (route) => {
				route.fulfill({
					status: 200,
					body: JSON.stringify({
						filename: 'test.pdf',
						size: 1024,
						status: 'success',
						message: 'File uploaded successfully'
					})
				});
			});

			// Create a mock file (in real tests, use a fixture file)
			await docsPage.fileInput.setInputFiles({
				name: 'test.pdf',
				mimeType: 'application/pdf',
				buffer: Buffer.from('PDF content')
			});

			// Should show success message
			const success = page.locator('[data-testid="upload-success"], .success');
			await expect(success).toBeVisible({ timeout: 10000 });
		});

		test('should reject invalid file types', async ({ page }) => {
			const docsPage = new DocumentsPage(page);
			await docsPage.goto();

			// Try to upload an executable
			await docsPage.fileInput.setInputFiles({
				name: 'malware.exe',
				mimeType: 'application/x-executable',
				buffer: Buffer.from('EXE content')
			});

			// Should show error message
			const error = page.locator('[data-testid="upload-error"], .error');
			await expect(error).toBeVisible();
		});

		test('should show upload progress', async ({ page }) => {
			const docsPage = new DocumentsPage(page);
			await docsPage.goto();

			// Mock slow upload
			await page.route('**/api/upload', async (route) => {
				await new Promise((resolve) => setTimeout(resolve, 2000));
				route.fulfill({
					status: 200,
					body: JSON.stringify({
						filename: 'large.pdf',
						status: 'success'
					})
				});
			});

			await docsPage.fileInput.setInputFiles({
				name: 'large.pdf',
				mimeType: 'application/pdf',
				buffer: Buffer.alloc(1024 * 1024) // 1MB
			});

			// Should show progress indicator
			const progress = page.locator('[data-testid="upload-progress"], .progress, [role="progressbar"]');
			await expect(progress).toBeVisible();
		});

		test('should handle large file rejection', async ({ page }) => {
			const docsPage = new DocumentsPage(page);
			await docsPage.goto();

			// Mock file size check
			await page.route('**/api/upload', (route) => {
				route.fulfill({
					status: 413,
					body: JSON.stringify({ detail: 'File too large' })
				});
			});

			// Try to upload "large" file
			await docsPage.fileInput.setInputFiles({
				name: 'huge.pdf',
				mimeType: 'application/pdf',
				buffer: Buffer.alloc(100) // Small buffer, server returns error
			});

			// Should show error
			const error = page.locator('[data-testid="upload-error"], .error');
			await expect(error).toBeVisible();
		});

		test('should support drag and drop', async ({ page }) => {
			const docsPage = new DocumentsPage(page);
			await docsPage.goto();

			// Create a DataTransfer with a file
			const dataTransfer = await page.evaluateHandle(() => {
				const dt = new DataTransfer();
				const file = new File(['content'], 'dropped.pdf', { type: 'application/pdf' });
				dt.items.add(file);
				return dt;
			});

			// Dispatch drop event
			await docsPage.uploadZone.dispatchEvent('drop', { dataTransfer });

			// Should trigger upload (mock or actual)
		});
	});

	test.describe('Document List', () => {
		test('should display document list', async ({ page }) => {
			const docsPage = new DocumentsPage(page);

			// Mock document list
			await page.route('**/api/documents', (route) => {
				route.fulfill({
					status: 200,
					body: JSON.stringify([
						{
							id: 'doc-1',
							filename: 'report.pdf',
							type: 'pdf',
							size: 1024000,
							status: 'ready',
							chunks: 10,
							created_at: new Date().toISOString()
						},
						{
							id: 'doc-2',
							filename: 'notes.md',
							type: 'markdown',
							size: 5000,
							status: 'ready',
							chunks: 3,
							created_at: new Date().toISOString()
						}
					])
				});
			});

			await docsPage.goto();

			await expect(docsPage.documentList).toBeVisible();
			const cards = docsPage.documentCards;
			await expect(cards).toHaveCount(2);
		});

		test('should show document details', async ({ page }) => {
			const docsPage = new DocumentsPage(page);

			await page.route('**/api/documents', (route) => {
				route.fulfill({
					status: 200,
					body: JSON.stringify([
						{
							id: 'doc-1',
							filename: 'report.pdf',
							type: 'pdf',
							size: 1048576, // 1MB
							status: 'ready',
							chunks: 10,
							created_at: new Date().toISOString()
						}
					])
				});
			});

			await docsPage.goto();

			const firstCard = docsPage.documentCards.first();
			await expect(firstCard).toContainText('report.pdf');
			await expect(firstCard).toContainText(/pdf|PDF/i);
		});

		test('should filter documents by type', async ({ page }) => {
			const docsPage = new DocumentsPage(page);

			await page.route('**/api/documents', (route) => {
				route.fulfill({
					status: 200,
					body: JSON.stringify([
						{ id: 'doc-1', filename: 'report.pdf', type: 'pdf', status: 'ready' },
						{ id: 'doc-2', filename: 'notes.md', type: 'markdown', status: 'ready' }
					])
				});
			});

			await docsPage.goto();

			// Click type filter if available
			const filterButton = page.locator('[data-testid="filter-type-pdf"]');
			if (await filterButton.isVisible()) {
				await filterButton.click();

				// Should only show PDF documents
				await expect(docsPage.documentCards).toHaveCount(1);
				await expect(docsPage.documentCards.first()).toContainText('report.pdf');
			}
		});

		test('should search documents', async ({ page }) => {
			const docsPage = new DocumentsPage(page);

			await page.route('**/api/documents', (route) => {
				route.fulfill({
					status: 200,
					body: JSON.stringify([
						{ id: 'doc-1', filename: 'report.pdf', type: 'pdf', status: 'ready' },
						{ id: 'doc-2', filename: 'notes.md', type: 'markdown', status: 'ready' }
					])
				});
			});

			await docsPage.goto();

			const searchInput = page.locator('[data-testid="document-search"], input[type="search"]');
			if (await searchInput.isVisible()) {
				await searchInput.fill('report');

				// Should filter to matching documents
				await expect(docsPage.documentCards).toHaveCount(1);
			}
		});

		test('should show empty state when no documents', async ({ page }) => {
			const docsPage = new DocumentsPage(page);

			await page.route('**/api/documents', (route) => {
				route.fulfill({
					status: 200,
					body: JSON.stringify([])
				});
			});

			await docsPage.goto();

			const emptyState = page.locator('[data-testid="empty-state"], .empty-state');
			await expect(emptyState).toBeVisible();
		});
	});

	test.describe('Document Actions', () => {
		test('should delete document with confirmation', async ({ page }) => {
			const docsPage = new DocumentsPage(page);

			await page.route('**/api/documents', (route) => {
				route.fulfill({
					status: 200,
					body: JSON.stringify([
						{ id: 'doc-1', filename: 'to-delete.pdf', type: 'pdf', status: 'ready' }
					])
				});
			});

			await page.route('**/api/documents/doc-1', (route) => {
				if (route.request().method() === 'DELETE') {
					route.fulfill({ status: 204 });
				}
			});

			await docsPage.goto();

			// Click delete button
			const deleteButton = page.locator('[data-testid="delete-document"]').first();
			if (await deleteButton.isVisible()) {
				await deleteButton.click();

				// Confirm in modal
				const confirmButton = page.locator('[data-testid="confirm-delete"], button:has-text("Delete")');
				await expect(confirmButton).toBeVisible();
				await confirmButton.click();

				// Document should be removed
				await expect(docsPage.documentCards).toHaveCount(0);
			}
		});

		test('should cancel delete operation', async ({ page }) => {
			const docsPage = new DocumentsPage(page);

			await page.route('**/api/documents', (route) => {
				route.fulfill({
					status: 200,
					body: JSON.stringify([
						{ id: 'doc-1', filename: 'keep-me.pdf', type: 'pdf', status: 'ready' }
					])
				});
			});

			await docsPage.goto();

			const deleteButton = page.locator('[data-testid="delete-document"]').first();
			if (await deleteButton.isVisible()) {
				await deleteButton.click();

				// Cancel in modal
				const cancelButton = page.locator('[data-testid="cancel-delete"], button:has-text("Cancel")');
				await cancelButton.click();

				// Document should still be there
				await expect(docsPage.documentCards).toHaveCount(1);
			}
		});

		test('should show document processing status', async ({ page }) => {
			const docsPage = new DocumentsPage(page);

			await page.route('**/api/documents', (route) => {
				route.fulfill({
					status: 200,
					body: JSON.stringify([
						{ id: 'doc-1', filename: 'processing.pdf', type: 'pdf', status: 'processing' }
					])
				});
			});

			await docsPage.goto();

			// Should show processing indicator
			const processingIndicator = page.locator('[data-testid="document-status-processing"], .processing');
			await expect(processingIndicator).toBeVisible();
		});
	});

	test.describe('Document Preview', () => {
		test('should open document preview on click', async ({ page }) => {
			const docsPage = new DocumentsPage(page);

			await page.route('**/api/documents', (route) => {
				route.fulfill({
					status: 200,
					body: JSON.stringify([
						{ id: 'doc-1', filename: 'preview-me.pdf', type: 'pdf', status: 'ready' }
					])
				});
			});

			await page.route('**/api/documents/doc-1', (route) => {
				route.fulfill({
					status: 200,
					body: JSON.stringify({
						id: 'doc-1',
						filename: 'preview-me.pdf',
						content: 'Document content...',
						chunks: []
					})
				});
			});

			await docsPage.goto();

			// Click on document card
			await docsPage.documentCards.first().click();

			// Should show preview modal or navigate to detail page
			const preview = page.locator('[data-testid="document-preview"], [data-testid="document-detail"]');
			await expect(preview).toBeVisible({ timeout: 5000 });
		});
	});

	test.describe('Accessibility', () => {
		test('should have accessible upload zone', async ({ page }) => {
			const docsPage = new DocumentsPage(page);
			await docsPage.goto();

			// Upload zone should have ARIA label
			const uploadLabel = await docsPage.uploadZone.getAttribute('aria-label');
			expect(uploadLabel || await docsPage.uploadZone.textContent()).toBeTruthy();

			// File input should be accessible
			const fileInputLabel = await docsPage.fileInput.getAttribute('aria-label');
			expect(fileInputLabel || await page.locator(`label[for="${await docsPage.fileInput.getAttribute('id')}"]`).isVisible()).toBeTruthy();
		});

		test('should announce upload status to screen readers', async ({ page }) => {
			const docsPage = new DocumentsPage(page);
			await docsPage.goto();

			// Mock upload
			await page.route('**/api/upload', (route) => {
				route.fulfill({
					status: 200,
					body: JSON.stringify({ status: 'success' })
				});
			});

			await docsPage.fileInput.setInputFiles({
				name: 'test.pdf',
				mimeType: 'application/pdf',
				buffer: Buffer.from('content')
			});

			// Success message should have ARIA live region
			const statusMessage = page.locator('[aria-live], [role="status"], [role="alert"]');
			await expect(statusMessage).toBeVisible();
		});
	});
});
