import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TaskItem from '../TaskItem';
import { api } from '@/lib/api';
import { Task } from '@/types';

// Mock API client
jest.mock('@/lib/api', () => ({
  api: {
    toggleTaskComplete: jest.fn(),
    deleteTask: jest.fn(),
    updateTask: jest.fn(),
  },
}));

// Mock window.confirm
const mockConfirm = jest.fn();
global.confirm = mockConfirm;

describe('TaskItem', () => {
  const mockTask: Task = {
    id: 1,
    user_id: 'user-123',
    title: 'Test Task',
    description: 'Test description',
    completed: false,
    priority: 'medium',
    due_date: '2025-12-31',
    tags: ['work', 'urgent'],
    created_at: '2025-12-01T00:00:00Z',
    updated_at: '2025-12-01T00:00:00Z',
  };

  const mockUserId = 'user-123';
  const mockOnSuccess = jest.fn();
  const mockOnError = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockConfirm.mockReturnValue(true);
  });

  describe('Rendering', () => {
    it('renders task in list view by default', () => {
      render(
        <TaskItem task={mockTask} userId={mockUserId} viewMode="list" />
      );

      expect(screen.getByRole('article')).toBeInTheDocument();
      expect(screen.getByText('Test Task')).toBeInTheDocument();
      expect(screen.getByText('Test description')).toBeInTheDocument();
    });

    it('renders task in card view', () => {
      render(
        <TaskItem task={mockTask} userId={mockUserId} viewMode="card" />
      );

      expect(screen.getByRole('article')).toBeInTheDocument();
      expect(screen.getByText('Test Task')).toBeInTheDocument();
    });

    it('renders priority badge', () => {
      render(<TaskItem task={mockTask} userId={mockUserId} />);

      expect(screen.getByText('Medium')).toBeInTheDocument();
    });

    it('renders tags', () => {
      render(<TaskItem task={mockTask} userId={mockUserId} />);

      expect(screen.getByText('work')).toBeInTheDocument();
      expect(screen.getByText('urgent')).toBeInTheDocument();
    });

    it('renders due date', () => {
      render(<TaskItem task={mockTask} userId={mockUserId} />);

      expect(screen.getByText(/2025-12-31/)).toBeInTheDocument();
    });

    it('shows overdue indicator for past due date', () => {
      const overdueTask = {
        ...mockTask,
        due_date: '2020-01-01',
      };

      render(<TaskItem task={overdueTask} userId={mockUserId} />);

      expect(screen.getByText(/Overdue/)).toBeInTheDocument();
    });

    it('renders without description if not provided', () => {
      const taskWithoutDescription = { ...mockTask, description: undefined };

      render(<TaskItem task={taskWithoutDescription} userId={mockUserId} />);

      expect(screen.queryByText('Test description')).not.toBeInTheDocument();
    });

    it('limits tags to 3 in card view', () => {
      const taskWithManyTags = {
        ...mockTask,
        tags: ['tag1', 'tag2', 'tag3', 'tag4', 'tag5'],
      };

      render(<TaskItem task={taskWithManyTags} userId={mockUserId} viewMode="card" />);

      expect(screen.getByText('tag1')).toBeInTheDocument();
      expect(screen.getByText('tag2')).toBeInTheDocument();
      expect(screen.getByText('tag3')).toBeInTheDocument();
      expect(screen.getByText('+2 more')).toBeInTheDocument();
      expect(screen.queryByText('tag4')).not.toBeInTheDocument();
    });
  });

  describe('Toggle Complete', () => {
    it('toggles task completion on checkbox click', async () => {
      const user = userEvent.setup();
      (api.toggleTaskComplete as jest.Mock).mockResolvedValue({
        success: true,
        data: { ...mockTask, completed: true },
      });

      render(<TaskItem task={mockTask} userId={mockUserId} />);

      const checkbox = screen.getByRole('button', { name: /mark as complete/i });
      await user.click(checkbox);

      await waitFor(() => {
        expect(api.toggleTaskComplete).toHaveBeenCalledWith(
          mockUserId,
          mockTask.id,
          true
        );
      });
    });

    it('shows optimistic update on toggle', async () => {
      const user = userEvent.setup();
      (api.toggleTaskComplete as jest.Mock).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () => resolve({ success: true, data: { ...mockTask, completed: true } }),
              100
            )
          )
      );

      render(<TaskItem task={mockTask} userId={mockUserId} />);

      const checkbox = screen.getByRole('button', { name: /mark as complete/i });
      await user.click(checkbox);

      // Should show optimistic update immediately
      expect(checkbox).toHaveAttribute('aria-pressed', 'true');
    });

    it('reverts optimistic update on error', async () => {
      const user = userEvent.setup();
      (api.toggleTaskComplete as jest.Mock).mockRejectedValue(
        new Error('Failed to toggle')
      );

      render(
        <TaskItem
          task={mockTask}
          userId={mockUserId}
          onError={mockOnError}
        />
      );

      const checkbox = screen.getByRole('button', { name: /mark as complete/i });
      await user.click(checkbox);

      await waitFor(() => {
        expect(checkbox).toHaveAttribute('aria-pressed', 'false');
        expect(mockOnError).toHaveBeenCalled();
      });
    });
  });

  describe('Delete Task', () => {
    it('deletes task with confirmation', async () => {
      const user = userEvent.setup();
      (api.deleteTask as jest.Mock).mockResolvedValue({ success: true });

      render(
        <TaskItem
          task={mockTask}
          userId={mockUserId}
          onSuccess={mockOnSuccess}
        />
      );

      const deleteButton = screen.getByLabelText(/delete task test task/i);
      await user.click(deleteButton);

      expect(mockConfirm).toHaveBeenCalledWith(
        'Are you sure you want to delete "Test Task"?'
      );

      await waitFor(() => {
        expect(api.deleteTask).toHaveBeenCalledWith(mockUserId, mockTask.id);
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });

    it('does not delete if confirmation is cancelled', async () => {
      const user = userEvent.setup();
      mockConfirm.mockReturnValue(false);

      render(<TaskItem task={mockTask} userId={mockUserId} />);

      const deleteButton = screen.getByLabelText(/delete task test task/i);
      await user.click(deleteButton);

      expect(mockConfirm).toHaveBeenCalled();
      expect(api.deleteTask).not.toHaveBeenCalled();
    });

    it('handles delete error', async () => {
      const user = userEvent.setup();
      (api.deleteTask as jest.Mock).mockRejectedValue(
        new Error('Failed to delete')
      );

      render(
        <TaskItem
          task={mockTask}
          userId={mockUserId}
          onError={mockOnError}
        />
      );

      const deleteButton = screen.getByLabelText(/delete task test task/i);
      await user.click(deleteButton);

      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalled();
      });
    });
  });

  describe('Inline Editing', () => {
    it('enters edit mode on double-click', async () => {
      const user = userEvent.setup();
      render(<TaskItem task={mockTask} userId={mockUserId} />);

      const title = screen.getByText('Test Task');
      await user.dblClick(title);

      const input = screen.getByRole('textbox', { name: /edit task title/i });
      expect(input).toBeInTheDocument();
      expect(input).toHaveValue('Test Task');
    });

    it('saves title on Enter key', async () => {
      const user = userEvent.setup();
      (api.updateTask as jest.Mock).mockResolvedValue({
        success: true,
        data: { ...mockTask, title: 'Updated Task' },
      });

      render(
        <TaskItem
          task={mockTask}
          userId={mockUserId}
          onSuccess={mockOnSuccess}
        />
      );

      const title = screen.getByText('Test Task');
      await user.dblClick(title);

      const input = screen.getByRole('textbox', { name: /edit task title/i });
      await user.clear(input);
      await user.type(input, 'Updated Task');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(api.updateTask).toHaveBeenCalledWith(mockUserId, mockTask.id, {
          title: 'Updated Task',
        });
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });

    it('cancels edit on Escape key', async () => {
      const user = userEvent.setup();
      render(<TaskItem task={mockTask} userId={mockUserId} />);

      const title = screen.getByText('Test Task');
      await user.dblClick(title);

      const input = screen.getByRole('textbox', { name: /edit task title/i });
      await user.clear(input);
      await user.type(input, 'Changed{Escape}');

      expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
      expect(screen.getByText('Test Task')).toBeInTheDocument();
    });

    it('does not save empty title', async () => {
      const user = userEvent.setup();
      render(<TaskItem task={mockTask} userId={mockUserId} />);

      const title = screen.getByText('Test Task');
      await user.dblClick(title);

      const input = screen.getByRole('textbox', { name: /edit task title/i });
      await user.clear(input);
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(api.updateTask).not.toHaveBeenCalled();
        expect(screen.getByText('Test Task')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      render(<TaskItem task={mockTask} userId={mockUserId} />);

      expect(screen.getByRole('article')).toHaveAttribute(
        'aria-label',
        'Task: Test Task'
      );
      expect(screen.getByRole('button', { name: /mark as complete/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/delete task test task/i)).toBeInTheDocument();
    });

    it('has proper aria-pressed for checkbox', () => {
      render(<TaskItem task={mockTask} userId={mockUserId} />);

      const checkbox = screen.getByRole('button', { name: /mark as complete/i });
      expect(checkbox).toHaveAttribute('aria-pressed', 'false');
    });

    it('disables buttons during operations', async () => {
      const user = userEvent.setup();
      (api.toggleTaskComplete as jest.Mock).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve({ success: true }), 100)
          )
      );

      render(<TaskItem task={mockTask} userId={mockUserId} />);

      const checkbox = screen.getByRole('button', { name: /mark as complete/i });
      const deleteButton = screen.getByLabelText(/delete task test task/i);

      await user.click(checkbox);

      expect(checkbox).toBeDisabled();
      expect(deleteButton).toBeDisabled();
    });
  });
});
