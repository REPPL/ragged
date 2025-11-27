/**
 * Theme Store
 * ragged WebUI v0.9.0
 *
 * Manages light/dark/high-contrast/system theme preference
 * WCAG 2.1 AA compliant high-contrast mode
 */

import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

export type ThemeMode = 'light' | 'dark' | 'high-contrast' | 'high-contrast-dark' | 'system';
export type ResolvedTheme = 'light' | 'dark' | 'high-contrast' | 'high-contrast-dark';

const STORAGE_KEY = 'ragged-theme';
const VALID_THEMES: ThemeMode[] = ['light', 'dark', 'high-contrast', 'high-contrast-dark', 'system'];

function getInitialTheme(): ThemeMode {
	if (!browser) return 'system';

	const stored = localStorage.getItem(STORAGE_KEY);
	if (stored && VALID_THEMES.includes(stored as ThemeMode)) {
		return stored as ThemeMode;
	}

	return 'system';
}

function getSystemTheme(): ResolvedTheme {
	if (!browser) return 'light';

	// Check for high contrast preference first (Windows high contrast mode)
	const prefersHighContrast = window.matchMedia('(prefers-contrast: more)').matches;
	const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

	if (prefersHighContrast) {
		return prefersDark ? 'high-contrast-dark' : 'high-contrast';
	}

	return prefersDark ? 'dark' : 'light';
}

function createThemeStore() {
	const { subscribe, set, update } = writable<ThemeMode>(getInitialTheme());

	// Listen for system theme changes
	if (browser) {
		// Listen for dark mode preference changes
		window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
			// Trigger reactivity for system theme
			update((mode) => mode);
		});

		// Listen for high contrast preference changes
		window.matchMedia('(prefers-contrast: more)').addEventListener('change', () => {
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
				// Cycle: light -> dark -> high-contrast -> high-contrast-dark -> system -> light
				const themeOrder: ThemeMode[] = ['light', 'dark', 'high-contrast', 'high-contrast-dark', 'system'];
				const currentIndex = themeOrder.indexOf(current);
				const next = themeOrder[(currentIndex + 1) % themeOrder.length];
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

	const resolved: ResolvedTheme = mode === 'system' ? getSystemTheme() : mode as ResolvedTheme;
	document.documentElement.setAttribute('data-theme', resolved);
}

export const themeMode = createThemeStore();

// Derived store for the actual applied theme
export const resolvedTheme = derived(themeMode, ($mode): ResolvedTheme => {
	return $mode === 'system' ? getSystemTheme() : $mode as ResolvedTheme;
});

// Check if dark mode is active (includes high-contrast-dark)
export const isDark = derived(resolvedTheme, ($theme) => $theme === 'dark' || $theme === 'high-contrast-dark');

// Check if high contrast mode is active
export const isHighContrast = derived(resolvedTheme, ($theme) => $theme === 'high-contrast' || $theme === 'high-contrast-dark');

// Helper to get human-readable theme name
export function getThemeLabel(mode: ThemeMode): string {
	const labels: Record<ThemeMode, string> = {
		light: 'Light',
		dark: 'Dark',
		'high-contrast': 'High Contrast',
		'high-contrast-dark': 'High Contrast Dark',
		system: 'System'
	};
	return labels[mode];
}
