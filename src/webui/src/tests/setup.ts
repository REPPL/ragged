/**
 * Test Setup
 * ragged WebUI v0.7.3
 *
 * Configure test environment
 */
import '@testing-library/jest-dom';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
	writable: true,
	value: (query: string) => ({
		matches: false,
		media: query,
		onchange: null,
		addListener: () => {},
		removeListener: () => {},
		addEventListener: () => {},
		removeEventListener: () => {},
		dispatchEvent: () => false
	})
});

// Mock localStorage
const localStorageMock = {
	store: {} as Record<string, string>,
	getItem(key: string) {
		return this.store[key] || null;
	},
	setItem(key: string, value: string) {
		this.store[key] = value;
	},
	removeItem(key: string) {
		delete this.store[key];
	},
	clear() {
		this.store = {};
	}
};

Object.defineProperty(window, 'localStorage', {
	value: localStorageMock
});

// Reset stores and localStorage between tests
beforeEach(() => {
	localStorageMock.clear();
});
