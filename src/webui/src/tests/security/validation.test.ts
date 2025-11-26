/**
 * Validation Utility Tests
 * ragged WebUI v0.7.4 - SEC-001
 */
import { describe, it, expect } from 'vitest';
import {
	sanitizeHtml,
	sanitizeRichHtml,
	sanitizeFilename,
	sanitizeUrlParam,
	validateEmail,
	validatePassword,
	validateText,
	validateUrl,
	validateNumber,
	validateFile,
	validateQuery,
	validateCollectionName,
	validateLoginForm,
	validateRegistrationForm,
	ALLOWED_DOCUMENT_TYPES,
	MAX_FILE_SIZE
} from '$utils';

describe('SEC-001: Input Validation & Sanitisation', () => {
	describe('sanitizeHtml', () => {
		it('should strip all HTML tags', () => {
			expect(sanitizeHtml('<script>alert("xss")</script>')).toBe('');
			expect(sanitizeHtml('<img src=x onerror=alert(1)>')).toBe('');
			expect(sanitizeHtml('Hello <b>World</b>')).toBe('Hello World');
		});

		it('should handle empty input', () => {
			expect(sanitizeHtml('')).toBe('');
			expect(sanitizeHtml(null as unknown as string)).toBe('');
		});

		it('should preserve plain text', () => {
			expect(sanitizeHtml('Hello World')).toBe('Hello World');
		});
	});

	describe('sanitizeRichHtml', () => {
		it('should allow safe formatting tags', () => {
			expect(sanitizeRichHtml('<b>Bold</b>')).toBe('<b>Bold</b>');
			expect(sanitizeRichHtml('<em>Italic</em>')).toBe('<em>Italic</em>');
			expect(sanitizeRichHtml('<code>code</code>')).toBe('<code>code</code>');
		});

		it('should strip dangerous tags', () => {
			expect(sanitizeRichHtml('<script>alert("xss")</script>')).toBe('');
			expect(sanitizeRichHtml('<iframe src="evil.com"></iframe>')).toBe('');
		});

		it('should strip event handlers', () => {
			expect(sanitizeRichHtml('<a onclick="evil()">Link</a>')).toBe('<a>Link</a>');
			expect(sanitizeRichHtml('<p onmouseover="evil()">Text</p>')).toBe('<p>Text</p>');
		});
	});

	describe('sanitizeFilename', () => {
		it('should remove dangerous characters', () => {
			expect(sanitizeFilename('file<>:"|?*.txt')).toBe('file_______.txt');
			expect(sanitizeFilename('../../../etc/passwd')).toBe('_/_/_/etc/passwd');
		});

		it('should prevent directory traversal', () => {
			expect(sanitizeFilename('..\\..\\windows\\system32')).toBe('_/_windows_system32');
		});

		it('should limit filename length', () => {
			const longName = 'a'.repeat(300) + '.txt';
			expect(sanitizeFilename(longName).length).toBeLessThanOrEqual(255);
		});
	});

	describe('sanitizeUrlParam', () => {
		it('should encode special characters', () => {
			expect(sanitizeUrlParam('hello world')).toBe('hello%20world');
			expect(sanitizeUrlParam('a=b&c=d')).toBe('a%3Db%26c%3Dd');
		});

		it('should trim whitespace', () => {
			expect(sanitizeUrlParam('  hello  ')).toBe('hello');
		});
	});

	describe('validateEmail', () => {
		it('should accept valid emails', () => {
			expect(validateEmail('user@example.com').valid).toBe(true);
			expect(validateEmail('user.name+tag@example.co.uk').valid).toBe(true);
		});

		it('should reject invalid emails', () => {
			expect(validateEmail('invalid').valid).toBe(false);
			expect(validateEmail('@example.com').valid).toBe(false);
			expect(validateEmail('user@').valid).toBe(false);
		});

		it('should return sanitised email', () => {
			expect(validateEmail('  USER@EXAMPLE.COM  ').sanitized).toBe('user@example.com');
		});

		it('should reject empty email', () => {
			expect(validateEmail('').valid).toBe(false);
			expect(validateEmail('   ').valid).toBe(false);
		});
	});

	describe('validatePassword', () => {
		it('should accept valid passwords', () => {
			expect(validatePassword('Password123').valid).toBe(true);
			expect(validatePassword('SecurePass1').valid).toBe(true);
		});

		it('should enforce minimum length', () => {
			expect(validatePassword('Short1').valid).toBe(false);
			expect(validatePassword('Short1', { minLength: 5 }).valid).toBe(true);
		});

		it('should enforce number requirement', () => {
			expect(validatePassword('NoNumbers', { requireNumbers: true }).valid).toBe(false);
		});

		it('should enforce special character requirement', () => {
			expect(validatePassword('NoSpecial1', { requireSpecial: true }).valid).toBe(false);
			expect(validatePassword('Special1!', { requireSpecial: true }).valid).toBe(true);
		});
	});

	describe('validateText', () => {
		it('should sanitise HTML and validate', () => {
			const result = validateText('<script>evil</script>Hello');
			expect(result.valid).toBe(true);
			expect(result.sanitized).toBe('Hello');
		});

		it('should enforce minimum length', () => {
			expect(validateText('ab', { minLength: 3 }).valid).toBe(false);
			expect(validateText('abc', { minLength: 3 }).valid).toBe(true);
		});

		it('should enforce maximum length', () => {
			expect(validateText('abcdef', { maxLength: 5 }).valid).toBe(false);
		});

		it('should enforce pattern', () => {
			expect(validateText('abc123', { pattern: /^[a-z]+$/ }).valid).toBe(false);
			expect(validateText('abc', { pattern: /^[a-z]+$/ }).valid).toBe(true);
		});
	});

	describe('validateUrl', () => {
		it('should accept valid URLs', () => {
			expect(validateUrl('https://example.com').valid).toBe(true);
			expect(validateUrl('http://example.com/path?query=1').valid).toBe(true);
		});

		it('should reject non-http protocols', () => {
			expect(validateUrl('javascript:alert(1)').valid).toBe(false);
			expect(validateUrl('file:///etc/passwd').valid).toBe(false);
		});

		it('should handle relative URLs when allowed', () => {
			expect(validateUrl('/path/to/page', { allowRelative: true }).valid).toBe(true);
			expect(validateUrl('//evil.com', { allowRelative: true }).valid).toBe(false);
		});
	});

	describe('validateNumber', () => {
		it('should accept valid numbers', () => {
			expect(validateNumber(42).valid).toBe(true);
			expect(validateNumber('3.14').valid).toBe(true);
		});

		it('should enforce range', () => {
			expect(validateNumber(5, { min: 10 }).valid).toBe(false);
			expect(validateNumber(15, { max: 10 }).valid).toBe(false);
			expect(validateNumber(10, { min: 5, max: 15 }).valid).toBe(true);
		});

		it('should enforce integer requirement', () => {
			expect(validateNumber(3.14, { integer: true }).valid).toBe(false);
			expect(validateNumber(42, { integer: true }).valid).toBe(true);
		});
	});

	describe('validateFile', () => {
		it('should accept valid files', () => {
			const file = new File(['content'], 'document.pdf', { type: 'application/pdf' });
			expect(validateFile(file).valid).toBe(true);
		});

		it('should reject files exceeding size limit', () => {
			const file = new File(['content'], 'large.pdf', { type: 'application/pdf' });
			Object.defineProperty(file, 'size', { value: MAX_FILE_SIZE + 1 });
			expect(validateFile(file).valid).toBe(false);
		});

		it('should reject disallowed file types', () => {
			const file = new File(['content'], 'script.exe', { type: 'application/x-executable' });
			expect(validateFile(file).valid).toBe(false);
		});

		it('should reject empty files', () => {
			const file = new File([], 'empty.pdf', { type: 'application/pdf' });
			expect(validateFile(file).valid).toBe(false);
		});
	});

	describe('validateQuery', () => {
		it('should accept valid queries', () => {
			expect(validateQuery('What is RAG?').valid).toBe(true);
		});

		it('should reject empty queries', () => {
			expect(validateQuery('').valid).toBe(false);
			expect(validateQuery('   ').valid).toBe(false);
		});

		it('should reject single character queries', () => {
			expect(validateQuery('a').valid).toBe(false);
		});

		it('should sanitise HTML in queries', () => {
			const result = validateQuery('<script>evil</script>What is RAG?');
			expect(result.valid).toBe(true);
			expect(result.sanitized).toBe('What is RAG?');
		});
	});

	describe('validateCollectionName', () => {
		it('should accept valid collection names', () => {
			expect(validateCollectionName('My Collection').valid).toBe(true);
			expect(validateCollectionName('collection-name_1').valid).toBe(true);
		});

		it('should reject invalid characters', () => {
			expect(validateCollectionName('collection@name').valid).toBe(false);
			expect(validateCollectionName('collection!name').valid).toBe(false);
		});

		it('should reject empty names', () => {
			expect(validateCollectionName('').valid).toBe(false);
		});
	});

	describe('validateLoginForm', () => {
		it('should validate complete form', () => {
			const result = validateLoginForm({
				email: 'user@example.com',
				password: 'password123'
			});
			expect(result.valid).toBe(true);
			expect(Object.keys(result.errors)).toHaveLength(0);
		});

		it('should return errors for invalid form', () => {
			const result = validateLoginForm({
				email: 'invalid',
				password: ''
			});
			expect(result.valid).toBe(false);
			expect(result.errors.email).toBeDefined();
			expect(result.errors.password).toBeDefined();
		});
	});

	describe('validateRegistrationForm', () => {
		it('should validate complete form', () => {
			const result = validateRegistrationForm({
				name: 'John Doe',
				email: 'john@example.com',
				password: 'Password123',
				confirmPassword: 'Password123'
			});
			expect(result.valid).toBe(true);
		});

		it('should detect password mismatch', () => {
			const result = validateRegistrationForm({
				name: 'John Doe',
				email: 'john@example.com',
				password: 'Password123',
				confirmPassword: 'DifferentPassword123'
			});
			expect(result.valid).toBe(false);
			expect(result.errors.confirmPassword).toBeDefined();
		});
	});
});
