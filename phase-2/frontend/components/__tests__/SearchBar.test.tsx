import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchBar from '../SearchBar';

describe('SearchBar', () => {
  const mockOnSearch = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('renders with default placeholder', () => {
    render(<SearchBar onSearch={mockOnSearch} />);

    const input = screen.getByPlaceholderText(
      'Search tasks by title or description...'
    );
    expect(input).toBeInTheDocument();
  });

  it('renders with custom placeholder', () => {
    render(
      <SearchBar onSearch={mockOnSearch} placeholder="Find your tasks..." />
    );

    const input = screen.getByPlaceholderText('Find your tasks...');
    expect(input).toBeInTheDocument();
  });

  it('calls onSearch with debounced value', async () => {
    const user = userEvent.setup({ delay: null });
    render(<SearchBar onSearch={mockOnSearch} debounceDelay={300} />);

    const input = screen.getByRole('searchbox');
    await user.type(input, 'test query');

    // Before debounce delay
    expect(mockOnSearch).not.toHaveBeenCalled();

    // Fast-forward time
    jest.advanceTimersByTime(300);

    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('test query');
    });
  });

  it('updates search value on input change', async () => {
    const user = userEvent.setup({ delay: null });
    render(<SearchBar onSearch={mockOnSearch} />);

    const input = screen.getByRole('searchbox') as HTMLInputElement;
    await user.type(input, 'new task');

    expect(input.value).toBe('new task');
  });

  it('shows clear button when there is text', async () => {
    const user = userEvent.setup({ delay: null });
    render(<SearchBar onSearch={mockOnSearch} />);

    const input = screen.getByRole('searchbox');

    // Initially no clear button (keyboard shortcut shown instead)
    expect(screen.queryByLabelText('Clear search')).not.toBeInTheDocument();

    // Type something
    await user.type(input, 'test');

    // Clear button should appear
    const clearButton = screen.getByLabelText('Clear search');
    expect(clearButton).toBeInTheDocument();
  });

  it('clears search when clear button is clicked', async () => {
    const user = userEvent.setup({ delay: null });
    render(<SearchBar onSearch={mockOnSearch} />);

    const input = screen.getByRole('searchbox') as HTMLInputElement;

    // Type something
    await user.type(input, 'test');
    expect(input.value).toBe('test');

    // Click clear button
    const clearButton = screen.getByLabelText('Clear search');
    await user.click(clearButton);

    // Input should be cleared
    expect(input.value).toBe('');
    expect(mockOnSearch).toHaveBeenCalledWith('');
  });

  it('focuses input when Ctrl+K is pressed', async () => {
    render(<SearchBar onSearch={mockOnSearch} />);

    const input = screen.getByRole('searchbox');

    // Press Ctrl+K
    await userEvent.keyboard('{Control>}k{/Control}');

    expect(input).toHaveFocus();
  });

  it('focuses input when Cmd+K is pressed', async () => {
    render(<SearchBar onSearch={mockOnSearch} />);

    const input = screen.getByRole('searchbox');

    // Press Cmd+K (Meta key for Mac)
    await userEvent.keyboard('{Meta>}k{/Meta}');

    expect(input).toHaveFocus();
  });

  it('has proper accessibility attributes', () => {
    render(<SearchBar onSearch={mockOnSearch} />);

    const input = screen.getByRole('searchbox');
    expect(input).toHaveAttribute('aria-label', 'Search tasks');
    expect(input).toHaveAttribute('aria-describedby', 'search-description');

    const description = screen.getByText(
      /Search tasks by title or description/
    );
    expect(description).toHaveAttribute('id', 'search-description');
  });

  it('has search role for accessibility', () => {
    const { container } = render(<SearchBar onSearch={mockOnSearch} />);

    const searchContainer = container.querySelector('[role="search"]');
    expect(searchContainer).toBeInTheDocument();
  });

  it('shows keyboard shortcut hint when input is empty', () => {
    render(<SearchBar onSearch={mockOnSearch} />);

    const kbdHint = screen.getByText('K');
    expect(kbdHint.closest('kbd')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <SearchBar onSearch={mockOnSearch} className="custom-class" />
    );

    const searchContainer = container.querySelector('[role="search"]');
    expect(searchContainer).toHaveClass('custom-class');
  });

  it('prevents default behavior on Ctrl+K', async () => {
    render(<SearchBar onSearch={mockOnSearch} />);

    const preventDefaultSpy = jest.fn();
    const event = new KeyboardEvent('keydown', {
      ctrlKey: true,
      key: 'k',
      bubbles: true,
    });
    Object.defineProperty(event, 'preventDefault', {
      value: preventDefaultSpy,
    });

    document.dispatchEvent(event);

    expect(preventDefaultSpy).toHaveBeenCalled();
  });

  it('debounces multiple rapid inputs', async () => {
    const user = userEvent.setup({ delay: null });
    render(<SearchBar onSearch={mockOnSearch} debounceDelay={300} />);

    const input = screen.getByRole('searchbox');

    // Type multiple characters rapidly
    await user.type(input, 'abc');

    // Before debounce delay, onSearch should not be called
    expect(mockOnSearch).not.toHaveBeenCalled();

    // Fast-forward time past debounce delay
    jest.advanceTimersByTime(300);

    // Should only call once with final value
    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledTimes(1);
      expect(mockOnSearch).toHaveBeenCalledWith('abc');
    });
  });
});
