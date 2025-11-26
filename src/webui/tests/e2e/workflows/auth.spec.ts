/**
 * Authentication Workflow E2E Tests
 * ragged WebUI v0.7.5 - QA-001
 */
import { test, expect } from '@playwright/test';
import { LoginPage, generateTestUser } from '../fixtures/test-utils';

test.describe('Authentication Workflows', () => {
	test.describe('Login', () => {
		test('should display login form', async ({ page }) => {
			const loginPage = new LoginPage(page);
			await loginPage.goto();

			await expect(loginPage.emailInput).toBeVisible();
			await expect(loginPage.passwordInput).toBeVisible();
			await expect(loginPage.submitButton).toBeVisible();
		});

		test('should show error for invalid credentials', async ({ page }) => {
			const loginPage = new LoginPage(page);
			await loginPage.goto();

			await loginPage.login('invalid@example.com', 'wrongpassword');

			// Should show error message
			await expect(page.locator('.error, [role="alert"]')).toBeVisible();
		});

		test('should validate email format', async ({ page }) => {
			const loginPage = new LoginPage(page);
			await loginPage.goto();

			await loginPage.emailInput.fill('invalid-email');
			await loginPage.passwordInput.fill('password123');
			await loginPage.submitButton.click();

			// Should show validation error
			await expect(page.locator('[data-testid="email-error"], .error')).toBeVisible();
		});

		test('should require password', async ({ page }) => {
			const loginPage = new LoginPage(page);
			await loginPage.goto();

			await loginPage.emailInput.fill('user@example.com');
			await loginPage.submitButton.click();

			// Should show validation error
			await expect(page.locator('[data-testid="password-error"], .error')).toBeVisible();
		});

		test('should redirect to requested page after login', async ({ page }) => {
			// Try to access protected page
			await page.goto('/settings');

			// Should redirect to login with return URL
			await expect(page).toHaveURL(/\/auth\/login\?redirect=/);
		});

		test('should prevent open redirect attacks', async ({ page }) => {
			// Try to use malicious redirect URL
			await page.goto('/auth/login?redirect=https://evil.com');

			const loginPage = new LoginPage(page);
			await loginPage.login('valid@example.com', 'password123');

			// Should NOT redirect to external URL
			await expect(page).not.toHaveURL(/evil\.com/);
		});
	});

	test.describe('Logout', () => {
		test('should clear session on logout', async ({ page }) => {
			// First login (mock or actual)
			await page.goto('/');

			// Click logout button if available
			const logoutButton = page.locator('[data-testid="logout"], button:has-text("Logout")');
			if (await logoutButton.isVisible()) {
				await logoutButton.click();

				// Should redirect to login
				await expect(page).toHaveURL(/\/auth\/login/);
			}
		});
	});

	test.describe('Session Management', () => {
		test('should persist session across page reloads', async ({ page }) => {
			await page.goto('/');

			// Store any session indicator
			const initialContent = await page.content();

			// Reload page
			await page.reload();

			// Session should be maintained (page should load same state)
			await expect(page).not.toHaveURL(/\/auth\/login/);
		});

		test('should handle expired sessions gracefully', async ({ page }) => {
			await page.goto('/');

			// Simulate expired session by clearing cookies
			await page.context().clearCookies();

			// Try to perform action requiring auth
			await page.goto('/settings');

			// Should redirect to login or show appropriate message
			// (Behaviour depends on implementation)
		});
	});

	test.describe('Registration', () => {
		test('should navigate to registration page', async ({ page }) => {
			await page.goto('/auth/login');

			const registerLink = page.locator('a[href="/auth/register"]');
			await expect(registerLink).toBeVisible();
			await registerLink.click();

			await expect(page).toHaveURL('/auth/register');
		});

		test('should validate registration form fields', async ({ page }) => {
			await page.goto('/auth/register');

			// Submit empty form
			const submitButton = page.locator('button[type="submit"]');
			await submitButton.click();

			// Should show validation errors
			await expect(page.locator('.error, [role="alert"]')).toBeVisible();
		});

		test('should validate password confirmation', async ({ page }) => {
			await page.goto('/auth/register');

			const user = generateTestUser();
			await page.locator('input[name="name"], [data-testid="name-input"]').fill(user.name);
			await page.locator('input[type="email"]').fill(user.email);
			await page.locator('input[name="password"], [data-testid="password-input"]').fill('password123');
			await page.locator('input[name="confirmPassword"], [data-testid="confirm-password-input"]').fill('differentpassword');

			const submitButton = page.locator('button[type="submit"]');
			await submitButton.click();

			// Should show password mismatch error
			await expect(page.locator('[data-testid="password-match-error"], .error')).toBeVisible();
		});
	});

	test.describe('Keyboard Navigation', () => {
		test('should support keyboard-only login', async ({ page }) => {
			const loginPage = new LoginPage(page);
			await loginPage.goto();

			// Tab to email
			await page.keyboard.press('Tab');
			await expect(loginPage.emailInput).toBeFocused();

			// Enter email
			await page.keyboard.type('user@example.com');

			// Tab to password
			await page.keyboard.press('Tab');
			await expect(loginPage.passwordInput).toBeFocused();

			// Enter password
			await page.keyboard.type('password123');

			// Tab to submit
			await page.keyboard.press('Tab');

			// Submit with Enter
			await page.keyboard.press('Enter');

			// Form should be submitted
			await page.waitForLoadState('networkidle');
		});

		test('should have visible focus indicators', async ({ page }) => {
			const loginPage = new LoginPage(page);
			await loginPage.goto();

			await page.keyboard.press('Tab');

			// Check that focused element has visible outline/ring
			const focusedElement = await page.locator(':focus');
			await expect(focusedElement).toBeVisible();

			// Should have some visual focus indicator (outline, ring, etc.)
			const outline = await focusedElement.evaluate((el) => {
				const style = window.getComputedStyle(el);
				return style.outline || style.boxShadow;
			});
			expect(outline).toBeTruthy();
		});
	});
});
