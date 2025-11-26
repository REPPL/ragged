/**
 * Sidebar Store
 * ragged WebUI v0.7.3
 *
 * Manages sidebar state (open/closed, width)
 */

import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

const STORAGE_KEY = 'ragged-sidebar';
const MOBILE_BREAKPOINT = 768;

interface SidebarState {
	isOpen: boolean;
	width: number;
	isMobile: boolean;
}

function getInitialState(): SidebarState {
	const isMobile = browser ? window.innerWidth < MOBILE_BREAKPOINT : false;

	if (!browser) {
		return { isOpen: true, width: 320, isMobile };
	}

	const stored = localStorage.getItem(STORAGE_KEY);
	if (stored) {
		try {
			const parsed = JSON.parse(stored);
			return {
				isOpen: isMobile ? false : parsed.isOpen ?? true,
				width: parsed.width ?? 320,
				isMobile
			};
		} catch {
			// Invalid stored data
		}
	}

	return { isOpen: !isMobile, width: 320, isMobile };
}

function createSidebarStore() {
	const { subscribe, set, update } = writable<SidebarState>(getInitialState());

	// Listen for window resize
	if (browser) {
		let resizeTimeout: ReturnType<typeof setTimeout>;

		window.addEventListener('resize', () => {
			clearTimeout(resizeTimeout);
			resizeTimeout = setTimeout(() => {
				const isMobile = window.innerWidth < MOBILE_BREAKPOINT;
				update((state) => {
					// Auto-close on mobile
					if (isMobile && !state.isMobile) {
						return { ...state, isMobile, isOpen: false };
					}
					// Keep state on desktop
					return { ...state, isMobile };
				});
			}, 100);
		});
	}

	function persist(state: SidebarState) {
		if (browser) {
			localStorage.setItem(STORAGE_KEY, JSON.stringify({
				isOpen: state.isOpen,
				width: state.width
			}));
		}
	}

	return {
		subscribe,

		toggle() {
			update((state) => {
				const newState = { ...state, isOpen: !state.isOpen };
				persist(newState);
				return newState;
			});
		},

		open() {
			update((state) => {
				const newState = { ...state, isOpen: true };
				persist(newState);
				return newState;
			});
		},

		close() {
			update((state) => {
				const newState = { ...state, isOpen: false };
				persist(newState);
				return newState;
			});
		},

		setWidth(width: number) {
			update((state) => {
				const newState = { ...state, width: Math.max(240, Math.min(480, width)) };
				persist(newState);
				return newState;
			});
		}
	};
}

export const sidebar = createSidebarStore();

// Derived stores
export const isSidebarOpen = derived(sidebar, ($sidebar) => $sidebar.isOpen);
export const sidebarWidth = derived(sidebar, ($sidebar) => $sidebar.width);
export const isMobile = derived(sidebar, ($sidebar) => $sidebar.isMobile);
