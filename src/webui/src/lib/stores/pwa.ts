/**
 * PWA Store
 * ragged WebUI v0.9.5
 *
 * Manages PWA installation state and offline status
 */

import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';

interface BeforeInstallPromptEvent extends Event {
	prompt(): Promise<void>;
	userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

interface PWAState {
	isInstallable: boolean;
	isInstalled: boolean;
	isOnline: boolean;
	isUpdateAvailable: boolean;
	deferredPrompt: BeforeInstallPromptEvent | null;
}

const initialState: PWAState = {
	isInstallable: false,
	isInstalled: false,
	isOnline: true,
	isUpdateAvailable: false,
	deferredPrompt: null
};

function createPWAStore() {
	const { subscribe, set, update } = writable<PWAState>(initialState);

	let registration: ServiceWorkerRegistration | null = null;

	function init() {
		if (!browser) return;

		// Check if already installed
		const isInstalled =
			window.matchMedia('(display-mode: standalone)').matches ||
			(window.navigator as any).standalone === true;

		update((state) => ({ ...state, isInstalled, isOnline: navigator.onLine }));

		// Listen for install prompt
		window.addEventListener('beforeinstallprompt', (e) => {
			e.preventDefault();
			update((state) => ({
				...state,
				isInstallable: true,
				deferredPrompt: e as BeforeInstallPromptEvent
			}));
		});

		// Listen for successful install
		window.addEventListener('appinstalled', () => {
			update((state) => ({
				...state,
				isInstalled: true,
				isInstallable: false,
				deferredPrompt: null
			}));
		});

		// Listen for online/offline status
		window.addEventListener('online', () => {
			update((state) => ({ ...state, isOnline: true }));
		});

		window.addEventListener('offline', () => {
			update((state) => ({ ...state, isOnline: false }));
		});

		// Register service worker
		registerServiceWorker();
	}

	async function registerServiceWorker() {
		if (!browser || !('serviceWorker' in navigator)) return;

		try {
			registration = await navigator.serviceWorker.register('/sw.js', {
				scope: '/'
			});

			// Check for updates
			registration.addEventListener('updatefound', () => {
				const newWorker = registration?.installing;
				if (!newWorker) return;

				newWorker.addEventListener('statechange', () => {
					if (
						newWorker.state === 'installed' &&
						navigator.serviceWorker.controller
					) {
						update((state) => ({ ...state, isUpdateAvailable: true }));
					}
				});
			});

			// Check for waiting worker (update ready)
			if (registration.waiting) {
				update((state) => ({ ...state, isUpdateAvailable: true }));
			}
		} catch (error) {
			console.error('[PWA] Service worker registration failed:', error);
		}
	}

	async function install() {
		const state = get({ subscribe });
		if (!state.deferredPrompt) return false;

		try {
			await state.deferredPrompt.prompt();
			const { outcome } = await state.deferredPrompt.userChoice;

			update((s) => ({
				...s,
				isInstallable: false,
				deferredPrompt: null
			}));

			return outcome === 'accepted';
		} catch (error) {
			console.error('[PWA] Install failed:', error);
			return false;
		}
	}

	async function update_app() {
		if (!registration?.waiting) return;

		registration.waiting.postMessage('skipWaiting');

		// Reload page after new service worker takes over
		navigator.serviceWorker.addEventListener('controllerchange', () => {
			window.location.reload();
		});
	}

	async function clearCache() {
		if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
			navigator.serviceWorker.controller.postMessage('clearCache');
		}
	}

	return {
		subscribe,
		init,
		install,
		update: update_app,
		clearCache
	};
}

export const pwa = createPWAStore();

// Derived stores for convenience
export const isInstallable = derived(pwa, ($pwa) => $pwa.isInstallable);
export const isInstalled = derived(pwa, ($pwa) => $pwa.isInstalled);
export const isOnline = derived(pwa, ($pwa) => $pwa.isOnline);
export const isUpdateAvailable = derived(pwa, ($pwa) => $pwa.isUpdateAvailable);
