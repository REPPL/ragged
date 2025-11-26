import type { PlaywrightTestConfig } from '@playwright/test';
import { devices } from '@playwright/test';

const config: PlaywrightTestConfig = {
	webServer: {
		command: 'npm run build && npm run preview',
		port: 4173,
		reuseExistingServer: !process.env.CI,
		timeout: 120000
	},
	testDir: 'tests',
	testMatch: /(.+\.)?(test|spec)\.[jt]s/,
	timeout: 30000,
	retries: process.env.CI ? 2 : 0,
	fullyParallel: true,
	forbidOnly: !!process.env.CI,
	workers: process.env.CI ? 1 : undefined,

	// Global settings
	use: {
		baseURL: 'http://localhost:4173',
		trace: 'on-first-retry',
		screenshot: 'only-on-failure',
		video: 'retain-on-failure',
		actionTimeout: 10000,
		navigationTimeout: 30000
	},

	// Test projects for cross-browser testing
	projects: [
		// Desktop browsers
		{
			name: 'chromium',
			use: { ...devices['Desktop Chrome'] },
			testDir: 'tests/e2e'
		},
		{
			name: 'firefox',
			use: { ...devices['Desktop Firefox'] },
			testDir: 'tests/e2e'
		},
		{
			name: 'webkit',
			use: { ...devices['Desktop Safari'] },
			testDir: 'tests/e2e'
		},

		// Mobile browsers
		{
			name: 'mobile-chrome',
			use: { ...devices['Pixel 5'] },
			testDir: 'tests/e2e'
		},
		{
			name: 'mobile-safari',
			use: { ...devices['iPhone 12'] },
			testDir: 'tests/e2e'
		},

		// Tablet
		{
			name: 'tablet',
			use: { ...devices['iPad (gen 7)'] },
			testDir: 'tests/e2e'
		},

		// Visual regression (Chromium only for consistency)
		{
			name: 'visual',
			use: {
				...devices['Desktop Chrome'],
				viewport: { width: 1280, height: 720 }
			},
			testDir: 'tests/visual'
		},

		// Accessibility testing
		{
			name: 'a11y',
			use: { ...devices['Desktop Chrome'] },
			testMatch: '**/accessibility.spec.ts'
		}
	],

	// Reporter configuration
	reporter: [
		['html', { open: 'never', outputFolder: 'playwright-report' }],
		['list'],
		['json', { outputFile: 'test-results/results.json' }],
		['junit', { outputFile: 'test-results/junit.xml' }]
	],

	// Output directories
	outputDir: 'test-results',

	// Snapshot configuration for visual regression
	expect: {
		toHaveScreenshot: {
			maxDiffPixelRatio: 0.01,
			animations: 'disabled',
			caret: 'hide'
		}
	}
};

export default config;
