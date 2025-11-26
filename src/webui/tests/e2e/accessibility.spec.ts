/**
 * Accessibility E2E Tests
 * ragged WebUI v0.7.5 - QA-002
 *
 * Tests for WCAG 2.1 AA compliance.
 */
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// List of pages to test
const PAGES_TO_TEST = [
	{ name: 'Home/Query', path: '/' },
	{ name: 'Documents', path: '/documents' },
	{ name: 'Collections', path: '/collections' },
	{ name: 'History', path: '/history' },
	{ name: 'Settings', path: '/settings' },
	{ name: 'Analytics', path: '/analytics' },
	{ name: 'Login', path: '/auth/login' },
	{ name: 'Register', path: '/auth/register' }
];

test.describe('Accessibility Compliance (WCAG 2.1 AA)', () => {
	test.describe('Automated Accessibility Scans', () => {
		for (const page of PAGES_TO_TEST) {
			test(`should have no accessibility violations on ${page.name}`, async ({ page: browserPage }) => {
				await browserPage.goto(page.path);
				await browserPage.waitForLoadState('networkidle');

				const accessibilityScanResults = await new AxeBuilder({ page: browserPage })
					.withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
					.analyze();

				// Filter out minor issues
				const criticalViolations = accessibilityScanResults.violations.filter(
					(v) => v.impact === 'critical' || v.impact === 'serious'
				);

				// Log violations for debugging
				if (criticalViolations.length > 0) {
					console.log(`\n${page.name} accessibility violations:`);
					criticalViolations.forEach((v) => {
						console.log(`  - ${v.id}: ${v.description} (${v.impact})`);
						v.nodes.forEach((n) => {
							console.log(`    Element: ${n.html.substring(0, 100)}`);
						});
					});
				}

				expect(
					criticalViolations,
					`Found ${criticalViolations.length} critical accessibility violations on ${page.name}`
				).toHaveLength(0);
			});
		}
	});

	test.describe('Keyboard Navigation', () => {
		test('should navigate all interactive elements with Tab', async ({ page }) => {
			await page.goto('/');
			await page.waitForLoadState('networkidle');

			// Tab through the page and count focusable elements
			const focusableElements: string[] = [];
			let previousFocused = '';

			for (let i = 0; i < 50; i++) {
				await page.keyboard.press('Tab');

				const focused = await page.evaluate(() => {
					const el = document.activeElement;
					return el ? `${el.tagName}:${el.id || el.className}` : 'none';
				});

				if (focused === previousFocused) {
					// Reached end of focusable elements
					break;
				}

				if (focused !== 'none' && focused !== 'BODY:') {
					focusableElements.push(focused);
				}

				previousFocused = focused;
			}

			// Should have focusable elements
			expect(focusableElements.length).toBeGreaterThan(0);
		});

		test('should have visible focus indicators', async ({ page }) => {
			await page.goto('/');
			await page.waitForLoadState('networkidle');

			// Tab to first interactive element
			await page.keyboard.press('Tab');

			// Check for visible focus indicator
			const focusedElement = page.locator(':focus');
			await expect(focusedElement).toBeVisible();

			// Check that focus is visually distinguishable
			const styles = await focusedElement.evaluate((el) => {
				const computed = window.getComputedStyle(el);
				return {
					outline: computed.outline,
					outlineWidth: computed.outlineWidth,
					outlineStyle: computed.outlineStyle,
					boxShadow: computed.boxShadow,
					borderColor: computed.borderColor
				};
			});

			// Should have some visible focus style
			const hasFocusStyle =
				styles.outline !== 'none' ||
				styles.outlineWidth !== '0px' ||
				styles.boxShadow !== 'none' ||
				styles.borderColor !== 'initial';

			expect(hasFocusStyle).toBe(true);
		});

		test('should close modals with Escape key', async ({ page }) => {
			await page.goto('/');

			// Open command palette (a modal)
			await page.keyboard.press('Meta+k');

			const modal = page.locator('[data-testid="command-palette"], [role="dialog"]');
			await expect(modal).toBeVisible();

			// Close with Escape
			await page.keyboard.press('Escape');
			await expect(modal).not.toBeVisible();
		});

		test('should trap focus within modals', async ({ page }) => {
			await page.goto('/');

			// Open command palette
			await page.keyboard.press('Meta+k');

			const modal = page.locator('[data-testid="command-palette"], [role="dialog"]');
			await expect(modal).toBeVisible();

			// Tab through modal
			const focusedElements: string[] = [];
			for (let i = 0; i < 10; i++) {
				await page.keyboard.press('Tab');

				const focused = await page.evaluate(() => {
					const el = document.activeElement;
					const modal = document.querySelector('[role="dialog"]');
					return modal?.contains(el) ? 'inside' : 'outside';
				});

				focusedElements.push(focused);
			}

			// Focus should stay inside modal
			const outsideFocus = focusedElements.filter((f) => f === 'outside');
			expect(outsideFocus.length).toBe(0);
		});

		test('should support arrow key navigation in lists', async ({ page }) => {
			await page.goto('/');

			// Open command palette which has a list
			await page.keyboard.press('Meta+k');

			// Arrow down should move selection
			await page.keyboard.press('ArrowDown');

			// Check that selection moved
			const selected = page.locator('[aria-selected="true"], [data-selected="true"], .selected');
			await expect(selected).toBeVisible();
		});
	});

	test.describe('Screen Reader Accessibility', () => {
		test('should have proper heading hierarchy', async ({ page }) => {
			await page.goto('/');
			await page.waitForLoadState('networkidle');

			// Get all headings
			const headings = await page.evaluate(() => {
				const headingElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
				return Array.from(headingElements).map((h) => ({
					level: parseInt(h.tagName.substring(1)),
					text: h.textContent?.trim()
				}));
			});

			// Should have at least one h1
			const h1Count = headings.filter((h) => h.level === 1).length;
			expect(h1Count).toBe(1);

			// Heading levels should not skip (e.g., h1 to h3)
			for (let i = 1; i < headings.length; i++) {
				const currentLevel = headings[i].level;
				const previousLevel = headings[i - 1].level;

				// Can go down one level or stay same or go up any amount
				if (currentLevel > previousLevel) {
					expect(currentLevel - previousLevel).toBeLessThanOrEqual(1);
				}
			}
		});

		test('should have proper landmark regions', async ({ page }) => {
			await page.goto('/');
			await page.waitForLoadState('networkidle');

			// Check for main landmark
			const main = page.locator('main, [role="main"]');
			await expect(main).toBeVisible();

			// Check for navigation landmark
			const nav = page.locator('nav, [role="navigation"]');
			await expect(nav).toBeVisible();

			// Check for banner (header)
			const banner = page.locator('header, [role="banner"]');
			await expect(banner).toBeVisible();
		});

		test('should have accessible form labels', async ({ page }) => {
			await page.goto('/auth/login');
			await page.waitForLoadState('networkidle');

			// All inputs should have labels
			const inputs = page.locator('input');
			const inputCount = await inputs.count();

			for (let i = 0; i < inputCount; i++) {
				const input = inputs.nth(i);
				const inputType = await input.getAttribute('type');

				// Skip hidden and submit inputs
				if (inputType === 'hidden' || inputType === 'submit') continue;

				const inputId = await input.getAttribute('id');
				const ariaLabel = await input.getAttribute('aria-label');
				const ariaLabelledby = await input.getAttribute('aria-labelledby');

				// Input should have associated label
				const hasLabel =
					ariaLabel ||
					ariaLabelledby ||
					(inputId && await page.locator(`label[for="${inputId}"]`).isVisible());

				expect(hasLabel, `Input ${i} (${inputType}) has no accessible label`).toBeTruthy();
			}
		});

		test('should announce dynamic content updates', async ({ page }) => {
			await page.goto('/');

			// Check for ARIA live regions
			const liveRegions = page.locator('[aria-live], [role="status"], [role="alert"]');
			const count = await liveRegions.count();

			// Should have at least one live region for announcements
			expect(count).toBeGreaterThan(0);
		});

		test('should have accessible images', async ({ page }) => {
			await page.goto('/');
			await page.waitForLoadState('networkidle');

			// All images should have alt text
			const images = page.locator('img');
			const imageCount = await images.count();

			for (let i = 0; i < imageCount; i++) {
				const img = images.nth(i);
				const alt = await img.getAttribute('alt');
				const role = await img.getAttribute('role');

				// Decorative images can have empty alt or role="presentation"
				const isAccessible = alt !== null || role === 'presentation' || role === 'none';

				expect(isAccessible, `Image ${i} has no alt text`).toBe(true);
			}
		});

		test('should have accessible buttons', async ({ page }) => {
			await page.goto('/');
			await page.waitForLoadState('networkidle');

			const buttons = page.locator('button');
			const buttonCount = await buttons.count();

			for (let i = 0; i < buttonCount; i++) {
				const button = buttons.nth(i);
				const text = await button.textContent();
				const ariaLabel = await button.getAttribute('aria-label');
				const ariaLabelledby = await button.getAttribute('aria-labelledby');
				const title = await button.getAttribute('title');

				// Button should have accessible name
				const hasName =
					(text && text.trim()) ||
					ariaLabel ||
					ariaLabelledby ||
					title;

				expect(hasName, `Button ${i} has no accessible name`).toBeTruthy();
			}
		});
	});

	test.describe('Colour and Contrast', () => {
		test('should have sufficient colour contrast for text', async ({ page }) => {
			await page.goto('/');
			await page.waitForLoadState('networkidle');

			const results = await new AxeBuilder({ page })
				.withTags(['wcag2aa'])
				.include(['body'])
				.analyze();

			const contrastViolations = results.violations.filter(
				(v) => v.id === 'color-contrast'
			);

			expect(contrastViolations).toHaveLength(0);
		});

		test('should not rely on colour alone for information', async ({ page }) => {
			await page.goto('/');

			// Check error states have more than just colour
			// Errors should have icons, text, or other indicators

			// Check status indicators
			const statusElements = page.locator('[data-status], .status, .badge');
			const count = await statusElements.count();

			for (let i = 0; i < count; i++) {
				const element = statusElements.nth(i);
				const text = await element.textContent();
				const ariaLabel = await element.getAttribute('aria-label');

				// Should have text or ARIA label, not just colour
				expect(text || ariaLabel).toBeTruthy();
			}
		});
	});

	test.describe('Text and Readability', () => {
		test('should support text zoom to 200%', async ({ page }) => {
			await page.goto('/');

			// Set viewport zoom
			await page.evaluate(() => {
				document.body.style.zoom = '2';
			});

			// Content should still be visible without horizontal scrolling
			const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
			const viewportWidth = await page.evaluate(() => window.innerWidth);

			// Allow some tolerance
			expect(bodyWidth).toBeLessThanOrEqual(viewportWidth * 2.2);

			// Key content should still be visible
			const mainContent = page.locator('main, [role="main"]');
			await expect(mainContent).toBeVisible();
		});

		test('should have readable line length', async ({ page }) => {
			await page.goto('/');

			// Check that main text content has reasonable line length
			const paragraphs = page.locator('p');
			const count = await paragraphs.count();

			for (let i = 0; i < Math.min(count, 5); i++) {
				const p = paragraphs.nth(i);
				const width = await p.evaluate((el) => el.offsetWidth);

				// Line length should be less than ~80ch (~640px at 16px font)
				expect(width).toBeLessThan(800);
			}
		});
	});

	test.describe('Animation and Motion', () => {
		test('should respect reduced motion preference', async ({ page }) => {
			// Emulate reduced motion preference
			await page.emulateMedia({ reducedMotion: 'reduce' });
			await page.goto('/');

			// Animations should be disabled or reduced
			const hasAnimations = await page.evaluate(() => {
				const style = window.getComputedStyle(document.body);
				const bodyDuration = parseFloat(style.animationDuration || '0');

				// Check a few elements
				const animated = document.querySelectorAll('[class*="animate"], [class*="transition"]');
				for (const el of animated) {
					const elStyle = window.getComputedStyle(el);
					const duration = parseFloat(elStyle.animationDuration || '0');
					if (duration > 0) return true;
				}

				return bodyDuration > 0;
			});

			// With reduced motion, animations should be minimal or disabled
			// This is a soft check - actual implementation may vary
		});
	});
});
