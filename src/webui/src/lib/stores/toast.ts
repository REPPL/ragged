/**
 * Toast Store
 * ragged WebUI v0.7.3
 *
 * Manages toast notifications
 */

import { writable, derived } from 'svelte/store';
import type { ToastMessage } from '$types';

const DEFAULT_DURATION = 5000;

function createToastStore() {
	const { subscribe, update } = writable<ToastMessage[]>([]);

	function generateId(): string {
		return `toast-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
	}

	function addToast(toast: Omit<ToastMessage, 'id'>): string {
		const id = generateId();
		const newToast: ToastMessage = {
			...toast,
			id,
			duration: toast.duration ?? DEFAULT_DURATION
		};

		update((toasts) => [...toasts, newToast]);

		// Auto-dismiss after duration
		if (newToast.duration && newToast.duration > 0) {
			setTimeout(() => {
				dismissToast(id);
			}, newToast.duration);
		}

		return id;
	}

	function dismissToast(id: string) {
		update((toasts) => toasts.filter((t) => t.id !== id));
	}

	function dismissAll() {
		update(() => []);
	}

	return {
		subscribe,
		add: addToast,
		dismiss: dismissToast,
		dismissAll,

		// Convenience methods
		success(title: string, message?: string) {
			return addToast({ type: 'success', title, message });
		},

		error(title: string, message?: string) {
			return addToast({ type: 'error', title, message, duration: 8000 });
		},

		warning(title: string, message?: string) {
			return addToast({ type: 'warning', title, message });
		},

		info(title: string, message?: string) {
			return addToast({ type: 'info', title, message });
		}
	};
}

export const toasts = createToastStore();

// Convenience exports
export const addToast = toasts.add;
export const dismissToast = toasts.dismiss;
export const dismissAllToasts = toasts.dismissAll;

// Derived store for toast count
export const toastCount = derived(toasts, ($toasts) => $toasts.length);
