/**
 * Theme Store
 * ragged WebUI v0.7.3
 *
 * Manages light/dark/system theme preference
 */

import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

type ThemeMode = 'light' | 'dark' | 'system';

const STORAGE_KEY = 'ragged-theme';

function getInitialTheme(): ThemeMode {
	if (!browser) return 'system';

	const stored = localStorage.getItem(STORAGE_KEY);
	if (stored && ['light', 'dark', 'system'].includes(stored)) {
		return stored as ThemeMode;
	}

	return 'system';
}

function getSystemTheme(): 'light' | 'dark' {
	if (!browser) return 'light';
	return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function createThemeStore() {
	const { subscribe, set, update } = writable<ThemeMode>(getInitialTheme());

	// Listen for system theme changes
	if (browser) {
		window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
			// Trigger reactivity for system theme
			update((mode) => mode);
		});
	}

	return {
		subscribe,

		setTheme(mode: ThemeMode) {
			set(mode);
			if (browser) {
				localStorage.setItem(STORAGE_KEY, mode);
				applyTheme(mode);
			}
		},

		toggle() {
			update((current) => {
				const next: ThemeMode = current === 'light' ? 'dark' : current === 'dark' ? 'system' : 'light';
				if (browser) {
					localStorage.setItem(STORAGE_KEY, next);
					applyTheme(next);
				}
				return next;
			});
		},

		init() {
			if (browser) {
				const mode = getInitialTheme();
				applyTheme(mode);
			}
		}
	};
}

function applyTheme(mode: ThemeMode) {
	if (!browser) return;

	const resolvedTheme = mode === 'system' ? getSystemTheme() : mode;
	document.documentElement.setAttribute('data-theme', resolvedTheme);
}

export const themeMode = createThemeStore();

// Derived store for the actual applied theme
export const resolvedTheme = derived(themeMode, ($mode) => {
	return $mode === 'system' ? getSystemTheme() : $mode;
});

// Check if dark mode is active
export const isDark = derived(resolvedTheme, ($theme) => $theme === 'dark');
