/**
 * Visual Regression Tests
 * ragged WebUI v0.7.5 - QA-005
 *
 * Screenshot comparison tests to detect unintended visual changes.
 */
import { test, expect } from '@playwright/test';

// Configure screenshot comparison options
const SCREENSHOT_OPTIONS = {
	fullPage: true,
	animations: 'disabled' as const,
	mask: [] as any[], // Dynamic content to mask
	maxDiffPixelRatio: 0.01 // Allow 1% pixel difference
};

test.describe('Visual Regression Tests', () => {
	test.describe('Light Theme', () => {
		test.beforeEach(async ({ page }) => {
			// Ensure light theme
			await page.emulateMedia({ colorScheme: 'light' });
		});

		test('Home page matches baseline', async ({ page }) => {
			await page.goto('/');
			await page.waitForLoadState('networkidle');

			// Mask dynamic content
			const masks = [
				page.locator('[data-testid="timestamp"]'),
				page.locator('[data-testid="user-avatar"]'),
				page.locator('.time, .date')
			];

			await expect(page).toHaveScreenshot('home-light.png', {
				...SCREENSHOT_OPTIONS,
				mask: masks
			});
		});

		test('Documents page matches baseline', async ({ page }) => {
			await page.goto('/documents');
			await page.waitForLoadState('networkidle');

			await expect(page).toHaveScreenshot('documents-light.png', SCREENSHOT_OPTIONS);
		});

		test('Collections page matches baseline', async ({ page }) => {
			await page.goto('/collections');
			await page.waitForLoadState('networkidle');

			await expect(page).toHaveScreenshot('collections-light.png', SCREENSHOT_OPTIONS);
		});

		test('Settings page matches baseline', async ({ page }) => {
			await page.goto('/settings');
			await page.waitForLoadState('networkidle');

			await expect(page).toHaveScreenshot('settings-light.png', SCREENSHOT_OPTIONS);
		});

		test('Analytics page matches baseline', async ({ page }) => {
			await page.goto('/analytics');
			await page.waitForLoadState('networkidle');

			await expect(page).toHaveScreenshot('analytics-light.png', SCREENSHOT_OPTIONS);
		});

		test('Login page matches baseline', async ({ page }) => {
			await page.goto('/auth/login');
			await page.waitForLoadState('networkidle');

			await expect(page).toHaveScreenshot('login-light.png', SCREENSHOT_OPTIONS);
		});
	});

	test.describe('Dark Theme', () => {
		test.beforeEach(async ({ page }) => {
			// Ensure dark theme
			await page.emulateMedia({ colorScheme: 'dark' });
		});

		test('Home page matches baseline', async ({ page }) => {
			await page.goto('/');
			await page.waitForLoadState('networkidle');

			await expect(page).toHaveScreenshot('home-dark.png', SCREENSHOT_OPTIONS);
		});

		test('Documents page matches baseline', async ({ page }) => {
			await page.goto('/documents');
			await page.waitForLoadState('networkidle');

			await expect(page).toHaveScreenshot('documents-dark.png', SCREENSHOT_OPTIONS);
		});

		test('Login page matches baseline', async ({ page }) => {
			await page.goto('/auth/login');
			await page.waitForLoadState('networkidle');

			await expect(page).toHaveScreenshot('login-dark.png', SCREENSHOT_OPTIONS);
		});
	});

	test.describe('Component States', () => {
		test('Empty state matches baseline', async ({ page }) => {
			// Mock empty documents list
			await page.route('**/api/documents', (route) => {
				route.fulfill({
					status: 200,
					body: JSON.stringify([])
				});
			});

			await page.goto('/documents');
			await page.waitForLoadState('networkidle');

			await expect(page).toHaveScreenshot('empty-state.png', SCREENSHOT_OPTIONS);
		});

		test('Loading state matches baseline', async ({ page }) => {
			// Mock slow response
			await page.route('**/api/documents', async (route) => {
				await new Promise((resolve) => setTimeout(resolve, 5000));
				route.fulfill({ status: 200, body: '[]' });
			});

			await page.goto('/documents');

			// Capture loading state
			await expect(page).toHaveScreenshot('loading-state.png', {
				...SCREENSHOT_OPTIONS,
				fullPage: false
			});
		});

		test('Error state matches baseline', async ({ page }) => {
			// Mock error
			await page.route('**/api/documents', (route) => {
				route.fulfill({
					status: 500,
					body: JSON.stringify({ detail: 'Server error' })
				});
			});

			await page.goto('/documents');
			await page.waitForLoadState('networkidle');

			await expect(page).toHaveScreenshot('error-state.png', SCREENSHOT_OPTIONS);
		});

		test('Modal open matches baseline', async ({ page }) => {
			await page.goto('/');
			await page.waitForLoadState('networkidle');

			// Open command palette
			await page.keyboard.press('Meta+k');
			await page.waitForTimeout(300); // Wait for animation

			await expect(page).toHaveScreenshot('modal-open.png', SCREENSHOT_OPTIONS);
		});

		test('Toast notification matches baseline', async ({ page }) => {
			await page.goto('/');
			await page.waitForLoadState('networkidle');

			// Trigger a toast (via mock or action)
			await page.evaluate(() => {
				// Dispatch custom event to show toast
				window.dispatchEvent(
					new CustomEvent('show-toast', {
						detail: { type: 'success', title: 'Success', message: 'Action completed' }
					})
				);
			});

			await page.waitForTimeout(300);

			const toast = page.locator('[data-testid="toast"]');
			if (await toast.isVisible()) {
				await expect(toast).toHaveScreenshot('toast-success.png');
			}
		});
	});

	test.describe('Responsive Layouts', () => {
		test('Desktop layout matches baseline', async ({ page }) => {
			await page.setViewportSize({ width: 1920, height: 1080 });
			await page.goto('/');
			await page.waitForLoadState('networkidle');

			await expect(page).toHaveScreenshot('desktop-layout.png', SCREENSHOT_OPTIONS);
		});

		test('Tablet layout matches baseline', async ({ page }) => {
			await page.setViewportSize({ width: 768, height: 1024 });
			await page.goto('/');
			await page.waitForLoadState('networkidle');

			await expect(page).toHaveScreenshot('tablet-layout.png', SCREENSHOT_OPTIONS);
		});

		test('Mobile layout matches baseline', async ({ page }) => {
			await page.setViewportSize({ width: 375, height: 667 });
			await page.goto('/');
			await page.waitForLoadState('networkidle');

			await expect(page).toHaveScreenshot('mobile-layout.png', SCREENSHOT_OPTIONS);
		});

		test('Sidebar collapsed matches baseline', async ({ page }) => {
			await page.setViewportSize({ width: 1024, height: 768 });
			await page.goto('/');
			await page.waitForLoadState('networkidle');

			// Toggle sidebar if available
			const sidebarToggle = page.locator('[data-testid="sidebar-toggle"]');
			if (await sidebarToggle.isVisible()) {
				await sidebarToggle.click();
				await page.waitForTimeout(300);

				await expect(page).toHaveScreenshot('sidebar-collapsed.png', SCREENSHOT_OPTIONS);
			}
		});
	});

	test.describe('Interactive Components', () => {
		test('Button hover state matches baseline', async ({ page }) => {
			await page.goto('/');
			await page.waitForLoadState('networkidle');

			const button = page.locator('button').first();
			await button.hover();
			await page.waitForTimeout(100);

			await expect(button).toHaveScreenshot('button-hover.png');
		});

		test('Input focus state matches baseline', async ({ page }) => {
			await page.goto('/auth/login');
			await page.waitForLoadState('networkidle');

			const input = page.locator('input[type="email"]');
			await input.focus();

			await expect(input).toHaveScreenshot('input-focus.png');
		});

		test('Dropdown open matches baseline', async ({ page }) => {
			await page.goto('/');
			await page.waitForLoadState('networkidle');

			const select = page.locator('select, [data-testid="dropdown"]').first();
			if (await select.isVisible()) {
				await select.click();
				await page.waitForTimeout(200);

				await expect(page).toHaveScreenshot('dropdown-open.png', SCREENSHOT_OPTIONS);
			}
		});
	});
});
