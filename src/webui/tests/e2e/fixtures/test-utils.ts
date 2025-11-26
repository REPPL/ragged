/**
 * E2E Test Utilities
 * ragged WebUI v0.7.5 - QA-001
 *
 * Shared utilities and page objects for Playwright E2E tests.
 */
import { type Page, type Locator, expect } from '@playwright/test';

// ============================================
// PAGE OBJECT MODELS
// ============================================

/**
 * Base page object with common utilities.
 */
export class BasePage {
	constructor(protected page: Page) {}

	/**
	 * Navigate to a path.
	 */
	async goto(path: string): Promise<void> {
		await this.page.goto(path);
	}

	/**
	 * Wait for page to be fully loaded.
	 */
	async waitForLoad(): Promise<void> {
		await this.page.waitForLoadState('networkidle');
	}

	/**
	 * Get toast notifications.
	 */
	getToast(): Locator {
		return this.page.locator('[data-testid="toast"]');
	}

	/**
	 * Wait for toast and verify message.
	 */
	async expectToast(type: 'success' | 'error' | 'warning' | 'info', message?: string): Promise<void> {
		const toast = this.getToast();
		await expect(toast).toBeVisible();
		await expect(toast).toHaveAttribute('data-type', type);
		if (message) {
			await expect(toast).toContainText(message);
		}
	}

	/**
	 * Close modal if open.
	 */
	async closeModal(): Promise<void> {
		const modal = this.page.locator('[data-testid="modal"]');
		if (await modal.isVisible()) {
			await this.page.keyboard.press('Escape');
			await expect(modal).not.toBeVisible();
		}
	}

	/**
	 * Open command palette.
	 */
	async openCommandPalette(): Promise<void> {
		await this.page.keyboard.press('Meta+k');
		await expect(this.page.locator('[data-testid="command-palette"]')).toBeVisible();
	}
}

/**
 * Login page object.
 */
export class LoginPage extends BasePage {
	async goto(): Promise<void> {
		await super.goto('/auth/login');
	}

	get emailInput(): Locator {
		return this.page.locator('input[type="email"]');
	}

	get passwordInput(): Locator {
		return this.page.locator('input[type="password"]');
	}

	get submitButton(): Locator {
		return this.page.locator('button[type="submit"]');
	}

	async login(email: string, password: string): Promise<void> {
		await this.emailInput.fill(email);
		await this.passwordInput.fill(password);
		await this.submitButton.click();
	}
}

/**
 * Query page object.
 */
export class QueryPage extends BasePage {
	async goto(): Promise<void> {
		await super.goto('/');
	}

	get queryInput(): Locator {
		return this.page.locator('[data-testid="query-input"]');
	}

	get submitButton(): Locator {
		return this.page.locator('[data-testid="query-submit"]');
	}

	get results(): Locator {
		return this.page.locator('[data-testid="query-results"]');
	}

	get resultCards(): Locator {
		return this.page.locator('[data-testid="result-card"]');
	}

	async submitQuery(query: string): Promise<void> {
		await this.queryInput.fill(query);
		await this.submitButton.click();
	}

	async waitForResults(): Promise<void> {
		await expect(this.results).toBeVisible();
	}
}

/**
 * Documents page object.
 */
export class DocumentsPage extends BasePage {
	async goto(): Promise<void> {
		await super.goto('/documents');
	}

	get uploadZone(): Locator {
		return this.page.locator('[data-testid="upload-zone"]');
	}

	get fileInput(): Locator {
		return this.page.locator('input[type="file"]');
	}

	get documentList(): Locator {
		return this.page.locator('[data-testid="document-list"]');
	}

	get documentCards(): Locator {
		return this.page.locator('[data-testid="document-card"]');
	}

	async uploadFile(filePath: string): Promise<void> {
		await this.fileInput.setInputFiles(filePath);
	}

	async waitForUpload(): Promise<void> {
		await this.page.waitForResponse((response) =>
			response.url().includes('/api/upload') && response.status() === 200
		);
	}
}

/**
 * Collections page object.
 */
export class CollectionsPage extends BasePage {
	async goto(): Promise<void> {
		await super.goto('/collections');
	}

	get createButton(): Locator {
		return this.page.locator('[data-testid="create-collection"]');
	}

	get collectionCards(): Locator {
		return this.page.locator('[data-testid="collection-card"]');
	}

	get nameInput(): Locator {
		return this.page.locator('[data-testid="collection-name"]');
	}

	get descriptionInput(): Locator {
		return this.page.locator('[data-testid="collection-description"]');
	}

	get submitButton(): Locator {
		return this.page.locator('[data-testid="collection-submit"]');
	}

	async createCollection(name: string, description?: string): Promise<void> {
		await this.createButton.click();
		await this.nameInput.fill(name);
		if (description) {
			await this.descriptionInput.fill(description);
		}
		await this.submitButton.click();
	}
}

/**
 * Settings page object.
 */
export class SettingsPage extends BasePage {
	async goto(): Promise<void> {
		await super.goto('/settings');
	}

	get themeToggle(): Locator {
		return this.page.locator('[data-testid="theme-toggle"]');
	}

	get saveButton(): Locator {
		return this.page.locator('[data-testid="save-settings"]');
	}
}

/**
 * History page object.
 */
export class HistoryPage extends BasePage {
	async goto(): Promise<void> {
		await super.goto('/history');
	}

	get historyItems(): Locator {
		return this.page.locator('[data-testid="history-item"]');
	}

	get clearButton(): Locator {
		return this.page.locator('[data-testid="clear-history"]');
	}
}

/**
 * Analytics page object.
 */
export class AnalyticsPage extends BasePage {
	async goto(): Promise<void> {
		await super.goto('/analytics');
	}

	get metricCards(): Locator {
		return this.page.locator('[data-testid="metric-card"]');
	}

	get performanceChart(): Locator {
		return this.page.locator('[data-testid="performance-chart"]');
	}

	get storageChart(): Locator {
		return this.page.locator('[data-testid="storage-chart"]');
	}
}

// ============================================
// TEST DATA GENERATORS
// ============================================

/**
 * Generate a unique test ID.
 */
export function generateTestId(): string {
	return `test-${Date.now()}-${Math.random().toString(36).substring(7)}`;
}

/**
 * Generate test user credentials.
 */
export function generateTestUser(): { email: string; password: string; name: string } {
	const id = generateTestId();
	return {
		email: `testuser-${id}@example.com`,
		password: 'TestPassword123!',
		name: `Test User ${id}`
	};
}

/**
 * Generate test collection data.
 */
export function generateTestCollection(): { name: string; description: string } {
	const id = generateTestId();
	return {
		name: `Test Collection ${id}`,
		description: `Description for test collection ${id}`
	};
}

// ============================================
// CUSTOM ASSERTIONS
// ============================================

/**
 * Assert element is accessible (has proper ARIA attributes).
 */
export async function expectAccessible(locator: Locator): Promise<void> {
	// Check for accessible name
	const accessibleName = await locator.getAttribute('aria-label') ||
		await locator.getAttribute('aria-labelledby') ||
		await locator.textContent();
	expect(accessibleName).toBeTruthy();

	// Check focusable if interactive
	const tagName = await locator.evaluate((el) => el.tagName.toLowerCase());
	if (['button', 'a', 'input', 'select', 'textarea'].includes(tagName)) {
		await expect(locator).toBeEnabled();
	}
}

/**
 * Assert page has no accessibility violations (basic check).
 */
export async function expectNoBasicA11yViolations(page: Page): Promise<void> {
	// Check for images without alt text
	const imagesWithoutAlt = await page.locator('img:not([alt])').count();
	expect(imagesWithoutAlt).toBe(0);

	// Check for buttons without text
	const buttonsWithoutText = await page.locator('button:not([aria-label]):empty').count();
	expect(buttonsWithoutText).toBe(0);

	// Check for inputs without labels
	const inputsWithoutLabels = await page.locator('input:not([aria-label]):not([id])').count();
	expect(inputsWithoutLabels).toBe(0);
}

// ============================================
// MOCK DATA
// ============================================

export const MOCK_DOCUMENTS = [
	{
		id: 'doc-1',
		filename: 'test-document.pdf',
		type: 'pdf',
		size: 1024000,
		status: 'ready',
		chunks: 10
	},
	{
		id: 'doc-2',
		filename: 'README.md',
		type: 'markdown',
		size: 5000,
		status: 'ready',
		chunks: 3
	}
];

export const MOCK_COLLECTIONS = [
	{
		id: 'col-1',
		name: 'Default Collection',
		description: 'The default document collection',
		document_count: 5,
		is_default: true
	},
	{
		id: 'col-2',
		name: 'Research Papers',
		description: 'Academic research papers',
		document_count: 12,
		is_default: false
	}
];
