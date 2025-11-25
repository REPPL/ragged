/**
 * Toast Store Tests
 * ragged WebUI v0.7.3
 */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { get } from 'svelte/store';
import { toasts, addToast, dismissToast, dismissAllToasts, toastCount } from '$lib/stores/toast';

describe('Toast Store', () => {
	beforeEach(() => {
		vi.useFakeTimers();
		dismissAllToasts();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	it('starts empty', () => {
		expect(get(toasts)).toHaveLength(0);
		expect(get(toastCount)).toBe(0);
	});

	it('can add a toast', () => {
		addToast({ type: 'success', title: 'Test', message: 'Test message' });
		expect(get(toasts)).toHaveLength(1);
		expect(get(toastCount)).toBe(1);
	});

	it('adds unique IDs to toasts', () => {
		addToast({ type: 'success', title: 'Test 1' });
		addToast({ type: 'error', title: 'Test 2' });

		const currentToasts = get(toasts);
		expect(currentToasts[0].id).not.toBe(currentToasts[1].id);
	});

	it('can dismiss a specific toast', () => {
		const id1 = addToast({ type: 'success', title: 'Test 1' });
		addToast({ type: 'error', title: 'Test 2' });

		dismissToast(id1);
		const currentToasts = get(toasts);
		expect(currentToasts).toHaveLength(1);
		expect(currentToasts[0].title).toBe('Test 2');
	});

	it('can dismiss all toasts', () => {
		addToast({ type: 'success', title: 'Test 1' });
		addToast({ type: 'error', title: 'Test 2' });
		addToast({ type: 'warning', title: 'Test 3' });

		dismissAllToasts();
		expect(get(toasts)).toHaveLength(0);
	});

	it('auto-dismisses after duration', () => {
		addToast({ type: 'success', title: 'Test', duration: 3000 });
		expect(get(toasts)).toHaveLength(1);

		vi.advanceTimersByTime(3000);
		expect(get(toasts)).toHaveLength(0);
	});

	it('uses default duration of 5000ms', () => {
		addToast({ type: 'info', title: 'Test' });
		expect(get(toasts)).toHaveLength(1);

		vi.advanceTimersByTime(4999);
		expect(get(toasts)).toHaveLength(1);

		vi.advanceTimersByTime(1);
		expect(get(toasts)).toHaveLength(0);
	});

	it('limits to 5 toasts', () => {
		for (let i = 0; i < 10; i++) {
			addToast({ type: 'info', title: `Test ${i}` });
		}

		expect(get(toasts).length).toBeLessThanOrEqual(5);
	});
});
