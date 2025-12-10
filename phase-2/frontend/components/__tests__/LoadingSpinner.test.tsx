import { render, screen } from '@testing-library/react';
import LoadingSpinner from '../LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders with default props', () => {
    render(<LoadingSpinner />);

    const status = screen.getByRole('status');
    expect(status).toBeInTheDocument();
    expect(status).toHaveAttribute('aria-label', 'Loading...');
    expect(status).toHaveAttribute('aria-live', 'polite');

    const srText = screen.getByText('Loading...');
    expect(srText).toHaveClass('sr-only');
  });

  it('renders with custom label', () => {
    render(<LoadingSpinner label="Fetching tasks..." />);

    const status = screen.getByRole('status');
    expect(status).toHaveAttribute('aria-label', 'Fetching tasks...');

    expect(screen.getByText('Fetching tasks...')).toBeInTheDocument();
  });

  it('renders small size correctly', () => {
    const { container } = render(<LoadingSpinner size="small" />);
    const spinner = container.querySelector('div[role="status"] > div');
    expect(spinner).toHaveClass('w-4', 'h-4', 'border-2');
  });

  it('renders medium size correctly', () => {
    const { container } = render(<LoadingSpinner size="medium" />);
    const spinner = container.querySelector('div[role="status"] > div');
    expect(spinner).toHaveClass('w-8', 'h-8', 'border-3');
  });

  it('renders large size correctly', () => {
    const { container } = render(<LoadingSpinner size="large" />);
    const spinner = container.querySelector('div[role="status"] > div');
    expect(spinner).toHaveClass('w-12', 'h-12', 'border-4');
  });

  it('renders with blue color by default', () => {
    const { container } = render(<LoadingSpinner />);
    const spinner = container.querySelector('div[role="status"] > div');
    expect(spinner).toHaveClass('border-blue-600', 'border-t-transparent');
  });

  it('renders with gray color', () => {
    const { container } = render(<LoadingSpinner color="gray" />);
    const spinner = container.querySelector('div[role="status"] > div');
    expect(spinner).toHaveClass('border-gray-600', 'border-t-transparent');
  });

  it('renders with white color', () => {
    const { container } = render(<LoadingSpinner color="white" />);
    const spinner = container.querySelector('div[role="status"] > div');
    expect(spinner).toHaveClass('border-white', 'border-t-transparent');
  });

  it('has animate-spin class', () => {
    const { container } = render(<LoadingSpinner />);
    const spinner = container.querySelector('div[role="status"] > div');
    expect(spinner).toHaveClass('animate-spin', 'rounded-full');
  });

  it('is accessible to screen readers', () => {
    render(<LoadingSpinner label="Loading tasks" />);

    // Check for screen reader text
    const srText = screen.getByText('Loading tasks');
    expect(srText).toBeInTheDocument();
    expect(srText).toHaveClass('sr-only');

    // Check for proper ARIA attributes
    const status = screen.getByRole('status');
    expect(status).toHaveAttribute('aria-live', 'polite');
  });
});
