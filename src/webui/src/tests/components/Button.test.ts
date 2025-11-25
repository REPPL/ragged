/**
 * Button Component Tests
 * ragged WebUI v0.7.3
 */
import { render, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import Button from '$lib/components/Button.svelte';

describe('Button', () => {
	it('renders with default props', () => {
		const { getByRole } = render(Button, { props: {} });
		const button = getByRole('button');
		expect(button).toBeInTheDocument();
		expect(button).toHaveClass('button');
		expect(button).toHaveClass('button--secondary');
		expect(button).toHaveClass('button--md');
	});

	it('renders with primary variant', () => {
		const { getByRole } = render(Button, { props: { variant: 'primary' } });
		expect(getByRole('button')).toHaveClass('button--primary');
	});

	it('renders with danger variant', () => {
		const { getByRole } = render(Button, { props: { variant: 'danger' } });
		expect(getByRole('button')).toHaveClass('button--danger');
	});

	it('renders with different sizes', () => {
		const { getByRole, rerender } = render(Button, { props: { size: 'sm' } });
		expect(getByRole('button')).toHaveClass('button--sm');

		rerender({ size: 'lg' });
		expect(getByRole('button')).toHaveClass('button--lg');
	});

	it('shows loading state', () => {
		const { getByRole } = render(Button, { props: { loading: true } });
		const button = getByRole('button');
		expect(button).toHaveClass('button--loading');
		expect(button).toBeDisabled();
	});

	it('can be disabled', () => {
		const { getByRole } = render(Button, { props: { disabled: true } });
		expect(getByRole('button')).toBeDisabled();
	});

	it('handles click events', async () => {
		const handleClick = vi.fn();
		const { getByRole, component } = render(Button);
		component.$on('click', handleClick);

		await fireEvent.click(getByRole('button'));
		expect(handleClick).toHaveBeenCalledOnce();
	});

	it('does not fire click when disabled', async () => {
		const handleClick = vi.fn();
		const { getByRole, component } = render(Button, { props: { disabled: true } });
		component.$on('click', handleClick);

		await fireEvent.click(getByRole('button'));
		expect(handleClick).not.toHaveBeenCalled();
	});

	it('does not fire click when loading', async () => {
		const handleClick = vi.fn();
		const { getByRole, component } = render(Button, { props: { loading: true } });
		component.$on('click', handleClick);

		await fireEvent.click(getByRole('button'));
		expect(handleClick).not.toHaveBeenCalled();
	});

	it('renders as submit button when type is submit', () => {
		const { getByRole } = render(Button, { props: { type: 'submit' } });
		expect(getByRole('button')).toHaveAttribute('type', 'submit');
	});

	it('renders full width when fullWidth is true', () => {
		const { getByRole } = render(Button, { props: { fullWidth: true } });
		expect(getByRole('button')).toHaveClass('button--full-width');
	});
});
