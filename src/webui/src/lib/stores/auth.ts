/**
 * Authentication Store
 * ragged WebUI v0.7.3
 *
 * Manages user authentication state
 */
import { writable, derived } from 'svelte/store';
import type { User, AuthState } from '$types';

// Initial state
const initialState: AuthState = {
	user: null,
	isAuthenticated: false,
	isLoading: true,
	error: null
};

// Create the auth store
function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>(initialState);

	return {
		subscribe,

		/**
		 * Set the authenticated user
		 */
		setUser: (user: User | null) => {
			update((state) => ({
				...state,
				user,
				isAuthenticated: !!user,
				isLoading: false,
				error: null
			}));
		},

		/**
		 * Set loading state
		 */
		setLoading: (isLoading: boolean) => {
			update((state) => ({
				...state,
				isLoading
			}));
		},

		/**
		 * Set error state
		 */
		setError: (error: string | null) => {
			update((state) => ({
				...state,
				error,
				isLoading: false
			}));
		},

		/**
		 * Clear authentication
		 */
		logout: () => {
			set({
				user: null,
				isAuthenticated: false,
				isLoading: false,
				error: null
			});
		},

		/**
		 * Reset to initial state
		 */
		reset: () => {
			set(initialState);
		}
	};
}

export const auth = createAuthStore();

// Derived stores for convenience
export const user = derived(auth, ($auth) => $auth.user);
export const isAuthenticated = derived(auth, ($auth) => $auth.isAuthenticated);
export const isAuthLoading = derived(auth, ($auth) => $auth.isLoading);
export const authError = derived(auth, ($auth) => $auth.error);

// Role-based access helpers
export const isAdmin = derived(auth, ($auth) => $auth.user?.role === 'admin');
export const isEditor = derived(
	auth,
	($auth) => $auth.user?.role === 'admin' || $auth.user?.role === 'editor'
);
export const canView = derived(auth, ($auth) => $auth.isAuthenticated);
