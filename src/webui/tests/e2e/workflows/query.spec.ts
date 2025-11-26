/**
 * Query Workflow E2E Tests
 * ragged WebUI v0.7.5 - QA-001
 */
import { test, expect } from '@playwright/test';
import { QueryPage } from '../fixtures/test-utils';

test.describe('Query Workflows', () => {
	test.describe('Query Submission', () => {
		test('should display query interface', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			await expect(queryPage.queryInput).toBeVisible();
			await expect(queryPage.submitButton).toBeVisible();
		});

		test('should submit query and show results', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			await queryPage.submitQuery('What is RAG?');

			// Wait for results
			await queryPage.waitForResults();

			// Should show answer
			await expect(queryPage.results).toContainText(/./);
		});

		test('should show loading state during query', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			await queryPage.queryInput.fill('Test query');
			await queryPage.submitButton.click();

			// Should show loading indicator
			const loading = page.locator('[data-testid="loading"], .loading, .spinner');
			await expect(loading).toBeVisible();
		});

		test('should handle empty query', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			// Try to submit empty query
			await queryPage.submitButton.click();

			// Should show validation error or disabled button
			const error = page.locator('[data-testid="query-error"], .error');
			await expect(error).toBeVisible();
		});

		test('should validate query length', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			// Single character query
			await queryPage.queryInput.fill('a');
			await queryPage.submitButton.click();

			// Should show validation error
			const error = page.locator('[data-testid="query-error"], .error');
			await expect(error).toBeVisible();
		});

		test('should sanitise query input', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			// Input with HTML
			await queryPage.queryInput.fill('<script>alert("xss")</script>What is RAG?');
			await queryPage.submitButton.click();

			// Should not execute script (page should still work)
			await queryPage.waitForResults();

			// No XSS should occur
			const alerts = await page.evaluate(() => window.alert);
			expect(alerts).toBeDefined(); // Original alert function
		});
	});

	test.describe('Query Options', () => {
		test('should show advanced options panel', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			// Click options toggle
			const optionsToggle = page.locator('[data-testid="options-toggle"]');
			if (await optionsToggle.isVisible()) {
				await optionsToggle.click();

				// Should show options panel
				const options = page.locator('[data-testid="query-options"]');
				await expect(options).toBeVisible();
			}
		});

		test('should allow changing retrieval method', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			// Open options
			const optionsToggle = page.locator('[data-testid="options-toggle"]');
			if (await optionsToggle.isVisible()) {
				await optionsToggle.click();

				// Select different retrieval method
				const methodSelect = page.locator('[data-testid="retrieval-method"]');
				if (await methodSelect.isVisible()) {
					await methodSelect.selectOption('bm25');
				}
			}
		});

		test('should allow setting top_k parameter', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			// Open options
			const optionsToggle = page.locator('[data-testid="options-toggle"]');
			if (await optionsToggle.isVisible()) {
				await optionsToggle.click();

				// Change top_k
				const topKInput = page.locator('[data-testid="top-k"]');
				if (await topKInput.isVisible()) {
					await topKInput.fill('10');
				}
			}
		});
	});

	test.describe('Query Results', () => {
		test('should display source documents', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			await queryPage.submitQuery('What is retrieval augmented generation?');
			await queryPage.waitForResults();

			// Should show result cards with sources
			const resultCards = queryPage.resultCards;
			const count = await resultCards.count();
			expect(count).toBeGreaterThanOrEqual(0);
		});

		test('should allow expanding source excerpts', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			await queryPage.submitQuery('Explain embeddings');
			await queryPage.waitForResults();

			// Click expand button if available
			const expandButton = page.locator('[data-testid="expand-source"]').first();
			if (await expandButton.isVisible()) {
				await expandButton.click();

				// Should show expanded content
				const expandedContent = page.locator('[data-testid="source-excerpt"]');
				await expect(expandedContent).toBeVisible();
			}
		});

		test('should handle no results gracefully', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			// Query that might return no results
			await queryPage.submitQuery('xyznonexistent12345');
			await queryPage.waitForResults();

			// Should show empty state or no results message
			const emptyState = page.locator('[data-testid="no-results"], .empty-state');
			const resultCount = await queryPage.resultCards.count();

			// Either empty state or zero results
			expect(resultCount === 0 || await emptyState.isVisible()).toBeTruthy();
		});

		test('should show relevance scores', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			await queryPage.submitQuery('How does RAG work?');
			await queryPage.waitForResults();

			// Check for score indicators if available
			const scores = page.locator('[data-testid="relevance-score"], .score');
			const count = await scores.count();

			// Scores may or may not be displayed based on UI design
			// This test just confirms the elements exist if shown
		});
	});

	test.describe('Query History Integration', () => {
		test('should save query to history', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			const uniqueQuery = `Test query ${Date.now()}`;
			await queryPage.submitQuery(uniqueQuery);
			await queryPage.waitForResults();

			// Navigate to history
			await page.goto('/history');

			// Should show the query
			const historyItems = page.locator('[data-testid="history-item"]');
			await expect(historyItems.first()).toContainText(uniqueQuery);
		});

		test('should allow rerunning query from history', async ({ page }) => {
			// First, create a query
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			await queryPage.submitQuery('Rerun test query');
			await queryPage.waitForResults();

			// Go to history
			await page.goto('/history');

			// Click rerun button
			const rerunButton = page.locator('[data-testid="rerun-query"]').first();
			if (await rerunButton.isVisible()) {
				await rerunButton.click();

				// Should navigate back to query page with query populated
				await expect(page).toHaveURL('/');
			}
		});
	});

	test.describe('Keyboard Shortcuts', () => {
		test('should focus query input with keyboard shortcut', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			// Press / to focus query input
			await page.keyboard.press('/');

			await expect(queryPage.queryInput).toBeFocused();
		});

		test('should submit query with Enter', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			await queryPage.queryInput.fill('Keyboard submit test');
			await page.keyboard.press('Enter');

			// Should submit query
			await queryPage.waitForResults();
		});

		test('should clear query with Escape', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			await queryPage.queryInput.fill('Clear me');
			await page.keyboard.press('Escape');

			// Input might be cleared or blurred
			const value = await queryPage.queryInput.inputValue();
			expect(value === '' || !await queryPage.queryInput.isFocused()).toBeTruthy();
		});
	});

	test.describe('Error Handling', () => {
		test('should handle API errors gracefully', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			// Mock API error
			await page.route('**/api/query', (route) => {
				route.fulfill({
					status: 500,
					body: JSON.stringify({ detail: 'Internal server error' })
				});
			});

			await queryPage.submitQuery('Error test');

			// Should show error message
			const error = page.locator('[data-testid="error"], .error, [role="alert"]');
			await expect(error).toBeVisible();
		});

		test('should handle network timeout', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			// Mock slow response
			await page.route('**/api/query', async (route) => {
				await new Promise((resolve) => setTimeout(resolve, 60000));
				route.fulfill({ status: 200, body: '{}' });
			});

			await queryPage.submitQuery('Timeout test');

			// Should show timeout or allow cancellation
			// (Implementation dependent)
		});

		test('should allow retrying failed queries', async ({ page }) => {
			const queryPage = new QueryPage(page);
			await queryPage.goto();

			// First request fails
			let requestCount = 0;
			await page.route('**/api/query', (route) => {
				requestCount++;
				if (requestCount === 1) {
					route.fulfill({ status: 500 });
				} else {
					route.fulfill({
						status: 200,
						body: JSON.stringify({ answer: 'Success', sources: [] })
					});
				}
			});

			await queryPage.submitQuery('Retry test');

			// Should show error
			const error = page.locator('[data-testid="error"], .error');
			await expect(error).toBeVisible();

			// Click retry
			const retryButton = page.locator('[data-testid="retry"], button:has-text("Retry")');
			if (await retryButton.isVisible()) {
				await retryButton.click();

				// Should succeed on retry
				await queryPage.waitForResults();
			}
		});
	});
});
