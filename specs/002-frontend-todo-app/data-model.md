# Data Model: Frontend Todo Application

## Frontend-Specific Types

### User Interface Types
```typescript
// User interface representations
interface UserUI {
  id: string;
  email: string;
  name: string;
  isAuthenticated: boolean;
}

// Task UI representation (matches backend model)
interface TaskUI {
  id: number;
  userId: string; // Comes from JWT token
  title: string;
  description?: string;
  completed: boolean;
  priority: 'low' | 'medium' | 'high';
  dueDate?: string; // ISO date string
  tags: string[];
  createdAt: string; // ISO datetime string
  updatedAt: string; // ISO datetime string
}

// Task form data (for creation/editing)
interface TaskFormData {
  title: string;
  description?: string;
  priority: 'low' | 'medium' | 'high';
  dueDate?: string; // ISO date string
  tags: string[];
}
```

### API Response Types
```typescript
// API response wrappers
interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

interface PaginatedResponse<T> {
  data: T[];
  meta: {
    total: number;
    page: number;
    limit: number;
    totalPages: number;
  };
}

// API request parameters
interface TaskQueryParams {
  status?: 'all' | 'pending' | 'completed';
  sort?: 'created' | 'title' | 'updated';
  search?: string;
  page?: number;
  limit?: number;
}
```

### Component State Types
```typescript
// Component state interfaces
interface TaskListState {
  tasks: TaskUI[];
  loading: boolean;
  error?: string;
  filters: {
    status: 'all' | 'pending' | 'completed';
    priority?: 'low' | 'medium' | 'high';
    search: string;
  };
  sortBy: 'created' | 'title' | 'updated';
  sortOrder: 'asc' | 'desc';
  currentPage: number;
  pageSize: number;
}

interface FormState {
  submitting: boolean;
  error?: string;
  success?: boolean;
}

interface NotificationState {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  visible: boolean;
  duration?: number;
}
```

### Theme and Preferences Types
```typescript
// UI theme and preferences
type Theme = 'light' | 'dark';

interface UserPreferences {
  theme: Theme;
  language: string;
  notificationsEnabled: boolean;
  keyboardShortcutsEnabled: boolean;
}
```

## Validation Rules

### Task Validation
- Title: Required, maximum 200 characters
- Description: Optional, maximum 1000 characters
- Priority: Must be one of 'low', 'medium', 'high'
- Due Date: If provided, must be a valid ISO date string
- Tags: Array of strings, each tag maximum 50 characters

### User Validation
- Email: Valid email format
- Password: Minimum 8 characters
- Name: Required, maximum 100 characters

## Component Relationships

### Page Components
- DashboardPage → Uses TaskList, TaskForm, FilterControls, SortControls, SearchBar, TaskStatistics
- SignupPage → Uses AuthForm component
- SigninPage → Uses AuthForm component

### Reusable Components
- TaskList ←→ TaskItem (contains multiple)
- TaskForm ←→ Various input components
- FilterControls ←→ Multiple filter sub-components
- SortControls ←→ Sorting selector
- ProtectedRoute ←→ All protected pages

## State Management Approach

### Server State
- Initial page data loaded in server components
- User session data from Better Auth

### Client State
- UI state (loading, error states) managed with useState
- Form state managed with useState or React Hook Form
- Theme preferences stored in localStorage
- API state managed through API client

### Authentication State
- Managed by Better Auth
- Session tokens automatically attached to API requests
- 401 error handling redirects to login