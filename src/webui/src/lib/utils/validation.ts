/**
 * Input Validation Utilities
 * ragged WebUI v0.7.4 - SEC-001
 *
 * Provides input validation and sanitisation for user inputs.
 * Uses DOMPurify for HTML sanitisation and custom validators for data types.
 */
import DOMPurify from 'dompurify';

// ============================================
// TYPES
// ============================================

export interface ValidationResult {
	valid: boolean;
	error?: string;
	sanitized?: string;
}

export interface ValidationOptions {
	required?: boolean;
	minLength?: number;
	maxLength?: number;
	pattern?: RegExp;
	customMessage?: string;
}

export interface FileValidationOptions {
	maxSize?: number; // bytes
	allowedTypes?: string[];
	allowedExtensions?: string[];
}

// ============================================
// TEXT SANITISATION
// ============================================

/**
 * Sanitise HTML content to prevent XSS attacks.
 * Strips all HTML tags by default, preserving only safe content.
 */
export function sanitizeHtml(input: string): string {
	if (!input) return '';
	return DOMPurify.sanitize(input, {
		ALLOWED_TAGS: [], // Strip all HTML
		ALLOWED_ATTR: []
	});
}

/**
 * Sanitise HTML content while allowing basic formatting tags.
 * Use for displaying user-generated content with formatting.
 */
export function sanitizeRichHtml(input: string): string {
	if (!input) return '';
	return DOMPurify.sanitize(input, {
		ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li', 'code', 'pre'],
		ALLOWED_ATTR: ['href', 'title', 'target', 'rel'],
		ADD_ATTR: ['target'],
		FORBID_ATTR: ['onclick', 'onerror', 'onload', 'onmouseover'],
		ALLOW_DATA_ATTR: false
	});
}

/**
 * Sanitise text for display, escaping HTML entities.
 */
export function escapeHtml(input: string): string {
	if (!input) return '';
	const div = document.createElement('div');
	div.textContent = input;
	return div.innerHTML;
}

/**
 * Sanitise input for URL parameters (encode special characters).
 */
export function sanitizeUrlParam(input: string): string {
	if (!input) return '';
	return encodeURIComponent(input.trim());
}

/**
 * Sanitise filename, removing potentially dangerous characters.
 */
export function sanitizeFilename(input: string): string {
	if (!input) return '';
	// Remove path separators and null bytes
	return input
		.replace(/[/\\:*?"<>|\x00-\x1f]/g, '_')
		.replace(/\.{2,}/g, '_') // Prevent directory traversal
		.trim()
		.substring(0, 255); // Limit length
}

// ============================================
// STRING VALIDATORS
// ============================================

/**
 * Validate email address format.
 */
export function validateEmail(email: string): ValidationResult {
	if (!email || !email.trim()) {
		return { valid: false, error: 'Email is required' };
	}

	const sanitized = email.trim().toLowerCase();
	// RFC 5322 compliant email regex (simplified)
	const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

	if (!emailRegex.test(sanitized)) {
		return { valid: false, error: 'Please enter a valid email address' };
	}

	if (sanitized.length > 254) {
		return { valid: false, error: 'Email address is too long' };
	}

	return { valid: true, sanitized };
}

/**
 * Validate password strength.
 */
export function validatePassword(
	password: string,
	options: { minLength?: number; requireNumbers?: boolean; requireSpecial?: boolean } = {}
): ValidationResult {
	const { minLength = 8, requireNumbers = true, requireSpecial = false } = options;

	if (!password) {
		return { valid: false, error: 'Password is required' };
	}

	if (password.length < minLength) {
		return { valid: false, error: `Password must be at least ${minLength} characters` };
	}

	if (password.length > 128) {
		return { valid: false, error: 'Password is too long (max 128 characters)' };
	}

	if (requireNumbers && !/\d/.test(password)) {
		return { valid: false, error: 'Password must contain at least one number' };
	}

	if (requireSpecial && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
		return { valid: false, error: 'Password must contain at least one special character' };
	}

	return { valid: true };
}

/**
 * Validate a text field with configurable options.
 */
export function validateText(input: string, options: ValidationOptions = {}): ValidationResult {
	const { required = true, minLength, maxLength, pattern, customMessage } = options;

	const sanitized = sanitizeHtml(input).trim();

	if (required && !sanitized) {
		return { valid: false, error: customMessage || 'This field is required' };
	}

	if (!required && !sanitized) {
		return { valid: true, sanitized: '' };
	}

	if (minLength && sanitized.length < minLength) {
		return { valid: false, error: customMessage || `Minimum ${minLength} characters required` };
	}

	if (maxLength && sanitized.length > maxLength) {
		return { valid: false, error: customMessage || `Maximum ${maxLength} characters allowed` };
	}

	if (pattern && !pattern.test(sanitized)) {
		return { valid: false, error: customMessage || 'Invalid format' };
	}

	return { valid: true, sanitized };
}

/**
 * Validate a URL.
 */
export function validateUrl(url: string, options: { allowRelative?: boolean } = {}): ValidationResult {
	if (!url || !url.trim()) {
		return { valid: false, error: 'URL is required' };
	}

	const trimmed = url.trim();

	// Check for relative URLs
	if (options.allowRelative && trimmed.startsWith('/')) {
		// Validate relative URL (no protocol-relative or absolute)
		if (trimmed.startsWith('//') || trimmed.includes('://')) {
			return { valid: false, error: 'Invalid URL format' };
		}
		return { valid: true, sanitized: trimmed };
	}

	// Validate absolute URL
	try {
		const parsed = new URL(trimmed);
		// Only allow http and https protocols
		if (!['http:', 'https:'].includes(parsed.protocol)) {
			return { valid: false, error: 'Only HTTP and HTTPS URLs are allowed' };
		}
		return { valid: true, sanitized: parsed.href };
	} catch {
		return { valid: false, error: 'Please enter a valid URL' };
	}
}

// ============================================
// NUMBER VALIDATORS
// ============================================

/**
 * Validate a number within a range.
 */
export function validateNumber(
	value: number | string,
	options: { min?: number; max?: number; integer?: boolean } = {}
): ValidationResult {
	const { min, max, integer = false } = options;

	const num = typeof value === 'string' ? parseFloat(value) : value;

	if (isNaN(num)) {
		return { valid: false, error: 'Please enter a valid number' };
	}

	if (integer && !Number.isInteger(num)) {
		return { valid: false, error: 'Please enter a whole number' };
	}

	if (min !== undefined && num < min) {
		return { valid: false, error: `Value must be at least ${min}` };
	}

	if (max !== undefined && num > max) {
		return { valid: false, error: `Value must be at most ${max}` };
	}

	return { valid: true, sanitized: String(num) };
}

// ============================================
// FILE VALIDATORS
// ============================================

/**
 * Allowed MIME types for document uploads.
 */
export const ALLOWED_DOCUMENT_TYPES = [
	'application/pdf',
	'text/plain',
	'text/markdown',
	'text/html',
	'application/msword',
	'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
];

/**
 * Allowed file extensions for document uploads.
 */
export const ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.txt', '.md', '.html', '.doc', '.docx'];

/**
 * Maximum file size (50MB default).
 */
export const MAX_FILE_SIZE = 50 * 1024 * 1024;

/**
 * Validate a file for upload.
 */
export function validateFile(
	file: File,
	options: FileValidationOptions = {}
): ValidationResult {
	const {
		maxSize = MAX_FILE_SIZE,
		allowedTypes = ALLOWED_DOCUMENT_TYPES,
		allowedExtensions = ALLOWED_DOCUMENT_EXTENSIONS
	} = options;

	if (!file) {
		return { valid: false, error: 'No file provided' };
	}

	// Check file size
	if (file.size > maxSize) {
		const maxMB = Math.round(maxSize / (1024 * 1024));
		return { valid: false, error: `File size exceeds ${maxMB}MB limit` };
	}

	if (file.size === 0) {
		return { valid: false, error: 'File is empty' };
	}

	// Check MIME type
	if (allowedTypes.length > 0 && !allowedTypes.includes(file.type)) {
		return { valid: false, error: 'File type not allowed' };
	}

	// Check file extension
	const extension = '.' + file.name.split('.').pop()?.toLowerCase();
	if (allowedExtensions.length > 0 && !allowedExtensions.includes(extension)) {
		return { valid: false, error: 'File extension not allowed' };
	}

	// Sanitise filename
	const sanitizedName = sanitizeFilename(file.name);
	if (sanitizedName !== file.name) {
		return { valid: true, sanitized: sanitizedName };
	}

	return { valid: true };
}

// ============================================
// QUERY VALIDATORS
// ============================================

/**
 * Validate a search/query string.
 */
export function validateQuery(query: string): ValidationResult {
	const sanitized = sanitizeHtml(query).trim();

	if (!sanitized) {
		return { valid: false, error: 'Please enter a query' };
	}

	if (sanitized.length < 2) {
		return { valid: false, error: 'Query must be at least 2 characters' };
	}

	if (sanitized.length > 2000) {
		return { valid: false, error: 'Query is too long (max 2000 characters)' };
	}

	return { valid: true, sanitized };
}

/**
 * Validate collection name.
 */
export function validateCollectionName(name: string): ValidationResult {
	const sanitized = sanitizeHtml(name).trim();

	if (!sanitized) {
		return { valid: false, error: 'Collection name is required' };
	}

	if (sanitized.length < 2) {
		return { valid: false, error: 'Name must be at least 2 characters' };
	}

	if (sanitized.length > 100) {
		return { valid: false, error: 'Name is too long (max 100 characters)' };
	}

	// Only allow alphanumeric, spaces, hyphens, underscores
	if (!/^[\w\s-]+$/.test(sanitized)) {
		return { valid: false, error: 'Name can only contain letters, numbers, spaces, hyphens, and underscores' };
	}

	return { valid: true, sanitized };
}

// ============================================
// FORM VALIDATION HELPERS
// ============================================

/**
 * Validate login form data.
 */
export function validateLoginForm(data: { email: string; password: string }): {
	valid: boolean;
	errors: Record<string, string>;
} {
	const errors: Record<string, string> = {};

	const emailResult = validateEmail(data.email);
	if (!emailResult.valid) {
		errors.email = emailResult.error!;
	}

	if (!data.password) {
		errors.password = 'Password is required';
	}

	return {
		valid: Object.keys(errors).length === 0,
		errors
	};
}

/**
 * Validate registration form data.
 */
export function validateRegistrationForm(data: {
	name: string;
	email: string;
	password: string;
	confirmPassword: string;
}): { valid: boolean; errors: Record<string, string> } {
	const errors: Record<string, string> = {};

	const nameResult = validateText(data.name, { minLength: 2, maxLength: 100 });
	if (!nameResult.valid) {
		errors.name = nameResult.error!;
	}

	const emailResult = validateEmail(data.email);
	if (!emailResult.valid) {
		errors.email = emailResult.error!;
	}

	const passwordResult = validatePassword(data.password);
	if (!passwordResult.valid) {
		errors.password = passwordResult.error!;
	}

	if (data.password !== data.confirmPassword) {
		errors.confirmPassword = 'Passwords do not match';
	}

	return {
		valid: Object.keys(errors).length === 0,
		errors
	};
}
