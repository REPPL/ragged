/**
 * Stores Index
 * ragged WebUI v0.9.0
 *
 * Barrel export for all stores
 */

export {
	themeMode,
	themeMode as theme, // Alias for backwards compatibility
	resolvedTheme,
	isDark,
	isHighContrast,
	getThemeLabel
} from './theme';
export { toasts, addToast, dismissToast, dismissAllToasts, toastCount } from './toast';
export {
	sidebar,
	isSidebarOpen,
	isSidebarOpen as sidebarOpen, // Alias for backwards compatibility
	sidebarWidth,
	isMobile
} from './sidebar';
export {
	auth,
	user,
	isAuthenticated,
	isAuthLoading,
	authError,
	isAdmin,
	isEditor,
	canView
} from './auth';
