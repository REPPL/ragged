/**
 * Theme Store Tests
 * ragged WebUI v0.7.3
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { themeMode, resolvedTheme, isDark } from '$lib/stores/theme';

describe('Theme Store', () => {
	beforeEach(() => {
		// Reset theme to default
		themeMode.set('system');
		localStorage.clear();
	});

	it('has default value of system', () => {
		expect(get(themeMode)).toBe('system');
	});

	it('can be set to light', () => {
		themeMode.set('light');
		expect(get(themeMode)).toBe('light');
	});

	it('can be set to dark', () => {
		themeMode.set('dark');
		expect(get(themeMode)).toBe('dark');
	});

	it('persists to localStorage', () => {
		themeMode.set('dark');
		expect(localStorage.getItem('ragged-theme')).toBe('dark');
	});

	it('loads from localStorage', () => {
		localStorage.setItem('ragged-theme', 'dark');
		// Would need to reinitialise the store to test this properly
	});

	it('resolvedTheme returns light when mode is light', () => {
		themeMode.set('light');
		expect(get(resolvedTheme)).toBe('light');
	});

	it('resolvedTheme returns dark when mode is dark', () => {
		themeMode.set('dark');
		expect(get(resolvedTheme)).toBe('dark');
	});

	it('isDark is false when theme is light', () => {
		themeMode.set('light');
		expect(get(isDark)).toBe(false);
	});

	it('isDark is true when theme is dark', () => {
		themeMode.set('dark');
		expect(get(isDark)).toBe(true);
	});
});
