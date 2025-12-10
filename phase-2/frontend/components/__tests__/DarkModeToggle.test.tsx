import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useTheme } from 'next-themes';
import DarkModeToggle from '../DarkModeToggle';

// Mock next-themes
jest.mock('next-themes', () => ({
  useTheme: jest.fn(),
}));

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  MoonIcon: () => <span data-testid="moon-icon">Moon</span>,
  SunIcon: () => <span data-testid="sun-icon">Sun</span>,
}));

describe('DarkModeToggle', () => {
  const mockSetTheme = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders moon icon when theme is light', () => {
    (useTheme as jest.Mock).mockReturnValue({
      theme: 'light',
      setTheme: mockSetTheme,
    });

    render(<DarkModeToggle />);

    expect(screen.getByTestId('moon-icon')).toBeInTheDocument();
    expect(screen.queryByTestId('sun-icon')).not.toBeInTheDocument();
  });

  it('renders sun icon when theme is dark', () => {
    (useTheme as jest.Mock).mockReturnValue({
      theme: 'dark',
      setTheme: mockSetTheme,
    });

    render(<DarkModeToggle />);

    expect(screen.getByTestId('sun-icon')).toBeInTheDocument();
    expect(screen.queryByTestId('moon-icon')).not.toBeInTheDocument();
  });

  it('has correct aria-label for light theme', () => {
    (useTheme as jest.Mock).mockReturnValue({
      theme: 'light',
      setTheme: mockSetTheme,
    });

    render(<DarkModeToggle />);

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Switch to dark mode');
  });

  it('has correct aria-label for dark theme', () => {
    (useTheme as jest.Mock).mockReturnValue({
      theme: 'dark',
      setTheme: mockSetTheme,
    });

    render(<DarkModeToggle />);

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Switch to light mode');
  });

  it('toggles from light to dark when clicked', async () => {
    const user = userEvent.setup();
    (useTheme as jest.Mock).mockReturnValue({
      theme: 'light',
      setTheme: mockSetTheme,
    });

    render(<DarkModeToggle />);

    const button = screen.getByRole('button');
    await user.click(button);

    expect(mockSetTheme).toHaveBeenCalledWith('dark');
  });

  it('toggles from dark to light when clicked', async () => {
    const user = userEvent.setup();
    (useTheme as jest.Mock).mockReturnValue({
      theme: 'dark',
      setTheme: mockSetTheme,
    });

    render(<DarkModeToggle />);

    const button = screen.getByRole('button');
    await user.click(button);

    expect(mockSetTheme).toHaveBeenCalledWith('light');
  });

  it('has screen reader text matching aria-label', () => {
    (useTheme as jest.Mock).mockReturnValue({
      theme: 'light',
      setTheme: mockSetTheme,
    });

    render(<DarkModeToggle />);

    const srText = screen.getByText('Switch to dark mode');
    expect(srText).toHaveClass('sr-only');
  });

  it('applies correct CSS classes for styling', () => {
    (useTheme as jest.Mock).mockReturnValue({
      theme: 'light',
      setTheme: mockSetTheme,
    });

    render(<DarkModeToggle />);

    const button = screen.getByRole('button');
    expect(button).toHaveClass('p-2', 'rounded-full');
    expect(button).toHaveClass('hover:bg-gray-200', 'dark:hover:bg-gray-700');
    expect(button).toHaveClass('focus:outline-none', 'focus:ring-2');
  });

  it('is keyboard accessible', async () => {
    const user = userEvent.setup();
    (useTheme as jest.Mock).mockReturnValue({
      theme: 'light',
      setTheme: mockSetTheme,
    });

    render(<DarkModeToggle />);

    const button = screen.getByRole('button');
    button.focus();
    expect(button).toHaveFocus();

    await user.keyboard('{Enter}');
    expect(mockSetTheme).toHaveBeenCalledWith('dark');
  });

  it('can be activated with spacebar', async () => {
    const user = userEvent.setup();
    (useTheme as jest.Mock).mockReturnValue({
      theme: 'dark',
      setTheme: mockSetTheme,
    });

    render(<DarkModeToggle />);

    const button = screen.getByRole('button');
    button.focus();

    await user.keyboard(' ');
    expect(mockSetTheme).toHaveBeenCalledWith('light');
  });
});
