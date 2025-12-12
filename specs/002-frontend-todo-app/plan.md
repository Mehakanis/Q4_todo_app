# Implementation Plan: Frontend Todo Application

**Branch**: `002-frontend-todo-app` | **Date**: 2025-12-07 | **Spec**: [specs/002-frontend-todo-app/spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-frontend-todo-app/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

A Next.js 16+ frontend application implementing a responsive todo list with authentication, task management, filtering/sorting/search, and advanced features. The application uses Better Auth for JWT-based authentication, a centralized API client at `/lib/api.ts` for backend communication, and follows server-first component architecture with client components only when needed for interactivity.

## Technical Context

**Language/Version**: TypeScript 5+ with strict mode
**Primary Dependencies**: Next.js 16+ (App Router), Better Auth with JWT plugin, Tailwind CSS, React 18+
**Storage**: N/A (uses backend API for persistence)
**Testing**: Jest/React Testing Library for frontend components
**Target Platform**: Web browsers (responsive: mobile, tablet, desktop)
**Project Type**: web - frontend application
**Performance Goals**: <3s page load, <1s search/filter, <500ms API calls
**Constraints**: WCAG 2.1 AA compliance, offline PWA capability, 1000+ task handling
**Scale/Scope**: Single-user per session, multiple concurrent users supported by backend

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **Principle II (Web-First Multi-User Application)**: Compliant - Next.js 16+ web app with responsive interface, all 5 Basic Level features implemented
✅ **Principle IV (Modular Monorepo Structure)**: Compliant - Frontend in `/frontend` directory as required
✅ **Principle V (Spec-Driven Development)**: Compliant - Following Spec-Kit Plus workflow
✅ **Principle XI (JWT Authentication)**: Compliant - Better Auth with JWT plugin as specified
✅ **Technical Standards**: Compliant - Next.js 16+, TypeScript, Tailwind CSS, Server Components default, Client Components when needed
✅ **Frontend File Structure**: Compliant - `/frontend/app/`, `/frontend/components/`, `/frontend/lib/api.ts` as specified
✅ **Frontend Patterns**: Compliant - Server components by default, Client components only for interactivity

*Post-design constitution check: All gates passed, research completed, ready for task generation.*

## API Contracts

### Backend API Endpoints (Integration Contract)

#### Authentication Endpoints
```
POST /api/auth/signup
- Request: { email: string, password: string, name: string }
- Response: { success: boolean, token: string, user: { id, email, name } }
- Headers: Content-Type: application/json
- Error: 400 (validation), 409 (email exists)

POST /api/auth/signin
- Request: { email: string, password: string }
- Response: { success: boolean, token: string, user: { id, email, name } }
- Headers: Content-Type: application/json
- Error: 400 (validation), 401 (invalid credentials)

POST /api/auth/signout
- Request: {}
- Response: { success: boolean }
- Headers: Authorization: Bearer {token}
- Error: 401 (invalid token)
```

#### Task Management Endpoints
```
GET /api/{user_id}/tasks
- Query Params: ?status=all|pending|completed, ?sort=created|title|updated, ?search=keyword, ?page=1, ?limit=20
- Response: {
    data: [
      {
        id: number,
        user_id: string,
        title: string,
        description?: string,
        completed: boolean,
        priority: 'low'|'medium'|'high',
        due_date?: string,
        tags: string[],
        created_at: string,
        updated_at: string
      }
    ],
    meta: { total: number, page: number, limit: number, totalPages: number }
  }
- Headers: Authorization: Bearer {token}
- Error: 401 (invalid token), 403 (user mismatch)

POST /api/{user_id}/tasks
- Request: {
    title: string (required),
    description?: string,
    priority?: 'low'|'medium'|'high',
    due_date?: string,
    tags?: string[]
  }
- Response: { data: TaskObject, success: boolean }
- Headers: Authorization: Bearer {token}, Content-Type: application/json
- Error: 400 (validation), 401 (invalid token), 403 (user mismatch)

GET /api/{user_id}/tasks/{id}
- Response: { data: TaskObject, success: boolean }
- Headers: Authorization: Bearer {token}
- Error: 401 (invalid token), 403 (user mismatch), 404 (task not found)

PUT /api/{user_id}/tasks/{id}
- Request: { title?, description?, priority?, due_date?, tags? }
- Response: { data: TaskObject, success: boolean }
- Headers: Authorization: Bearer {token}, Content-Type: application/json
- Error: 400 (validation), 401 (invalid token), 403 (user mismatch), 404 (task not found)

DELETE /api/{user_id}/tasks/{id}
- Response: { success: boolean, message: string }
- Headers: Authorization: Bearer {token}
- Error: 401 (invalid token), 403 (user mismatch), 404 (task not found)

PATCH /api/{user_id}/tasks/{id}/complete
- Request: { completed: boolean }
- Response: { data: TaskObject, success: boolean }
- Headers: Authorization: Bearer {token}, Content-Type: application/json
- Error: 400 (validation), 401 (invalid token), 403 (user mismatch), 404 (task not found)
```

#### Frontend API Client Contract (`/lib/api.ts`)
```typescript
interface ApiClient {
  // Authentication methods
  signup(userData: { email: string, password: string, name: string }): Promise<ApiResponse<User>>;
  signin(credentials: { email: string, password: string }): Promise<ApiResponse<User>>;
  signout(): Promise<ApiResponse<void>>;

  // Task methods
  getTasks(userId: string, queryParams?: TaskQueryParams): Promise<ApiResponse<PaginatedResponse<TaskUI>>>;
  createTask(userId: string, taskData: TaskFormData): Promise<ApiResponse<TaskUI>>;
  getTaskById(userId: string, taskId: number): Promise<ApiResponse<TaskUI>>;
  updateTask(userId: string, taskId: number, taskData: Partial<TaskFormData>): Promise<ApiResponse<TaskUI>>;
  deleteTask(userId: string, taskId: number): Promise<ApiResponse<void>>;
  toggleTaskComplete(userId: string, taskId: number, completed: boolean): Promise<ApiResponse<TaskUI>>;

  // Export/Import methods
  exportTasks(userId: string, format: 'csv' | 'json'): Promise<Blob>;
  importTasks(userId: string, file: File): Promise<ApiResponse<{ imported: number, errors: number }>>;
}

interface TaskQueryParams {
  status?: 'all' | 'pending' | 'completed';
  sort?: 'created' | 'title' | 'updated';
  search?: string;
  page?: number;
  limit?: number;
}

interface ApiResponse<T> {
  data?: T;
  success: boolean;
  message?: string;
  error?: {
    code: string;
    message: string;
  };
}
```

## Implementation Strategy

### Phase 1: Foundation (setup, API client, Better Auth)
- Set up Next.js 16+ project with TypeScript and Tailwind CSS
- Configure Better Auth with JWT plugin
- Implement centralized API client at `/lib/api.ts`
- Set up basic project structure and configuration

### Phase 2: Authentication (signup, signin)
- Create signup page with form validation
- Create signin page with form validation
- Implement ProtectedRoute component
- Add JWT token management and error handling

### Phase 3: Basic Tasks (CRUD operations)
- Create dashboard page with protected route
- Implement TaskForm, TaskList, TaskItem components
- Connect to backend API endpoints (GET, POST, PUT, DELETE, PATCH)
- Add loading states and error handling

### Phase 4: Organization (filter, sort, search)
- Implement FilterControls component
- Implement SortControls component
- Implement SearchBar component
- Integrate query parameters for filtering, sorting, and search

### Phase 5: UX (responsive, dark mode, accessibility)
- Implement responsive design with Tailwind breakpoints
- Add dark mode toggle with theme persistence
- Ensure WCAG 2.1 AA compliance
- Add keyboard shortcuts and accessibility features

### Phase 6: Advanced (export, drag-drop, undo/redo)
- Implement ExportImportControls component
- Add drag-and-drop reordering with @dnd-kit/core
- Implement undo/redo functionality with useReducer
- Add bulk operations and inline editing

### Phase 7: Enhanced (real-time, offline)
- Implement real-time updates with polling (5-second intervals)
- Add PWA functionality with service workers
- Implement offline data storage and sync

### Phase 8: Polish (tests, optimization)
- Add comprehensive tests (unit, integration, E2E)
- Optimize performance and bundle size
- Conduct accessibility and security audits
- Prepare for deployment

**Dependencies**: Each phase depends on the previous phase's completion. Authentication must be working before basic tasks, and basic tasks must be working before organization features.

## Risk Analysis

### Top 3 Risks:

1. **Backend API Changes**
   - **Blast Radius**: Affects all API client methods and error handling
   - **Mitigation Strategy**: Use strongly typed interfaces, implement comprehensive error handling, mock API for development
   - **Kill Switch**: Feature flags to disable affected functionality temporarily

2. **JWT Expiration During Long Sessions**
   - **Blast Radius**: Affects all authenticated user operations
   - **Mitigation Strategy**: Implement automatic token refresh, graceful re-authentication, user warnings before expiration
   - **Kill Switch**: Automatic redirect to login with return URL preservation

3. **Performance Degradation with Large Task Lists (1000+)**
   - **Blast Radius**: Affects dashboard loading, filtering, and search performance
   - **Mitigation Strategy**: Implement pagination, virtual scrolling, lazy loading, caching strategies
   - **Kill Switch**: Progressive loading with "Load More" functionality

## Success Metrics

### Mapping Success Criteria (SC-001 to SC-010):

1. **SC-001**: Account registration under 2 minutes
   - **Validation**: Measure time from page load to dashboard redirect, test with realistic form data
   - **Test**: Automated timing test in E2E suite

2. **SC-002**: Create new task in under 30 seconds
   - **Validation**: Measure from form focus to task appearing in list
   - **Test**: Performance monitoring in E2E test

3. **SC-003**: Task list loads in under 3 seconds for 1000+ tasks
   - **Validation**: Test with mock data of 1000+ tasks, measure render time
   - **Test**: Synthetic performance tests with large datasets

4. **SC-004**: Seamless responsive experience across devices
   - **Validation**: Manual testing on mobile, tablet, desktop; responsive design verification
   - **Test**: Visual regression tests across breakpoints

5. **SC-005**: 95% success rate on primary operations
   - **Validation**: Track user success/failure rates in production
   - **Test**: Comprehensive error boundary and error handling tests

6. **SC-006**: Real-time filtering/search under 1 second
   - **Validation**: Measure query execution time with large datasets
   - **Test**: Performance benchmarks with simulated data

7. **SC-007**: Export/import completes within 10 seconds for 1000 tasks
   - **Validation**: Test with 1000-task datasets
   - **Test**: Performance tests for CSV/JSON export/import

8. **SC-008**: 90% of users find dark mode toggle
   - **Validation**: UI/UX testing and analytics tracking
   - **Test**: Usability tests with task completion metrics

9. **SC-009**: Offline sync within 5 seconds of connection
   - **Validation**: Test offline functionality and sync timing
   - **Test**: Network simulation tests in service worker

10. **SC-010**: Real-time dashboard updates within 1 second
    - **Validation**: Measure polling interval and update propagation
    - **Test**: Timing tests with simulated backend updates

### Quality Metrics:
- Test coverage: 80%+ for all components
- Error rate: <1% for critical operations
- Accessibility: 95%+ score on axe-core tests
- Performance: Lighthouse scores >90 in all categories

### Definition of Done Checklist:
- [ ] All acceptance tests pass
- [ ] Performance benchmarks met
- [ ] Accessibility standards met
- [ ] Security audit passed
- [ ] Cross-browser compatibility verified
- [ ] Mobile responsiveness verified
- [ ] Error handling implemented
- [ ] Loading states implemented

## Acceptance Scenarios

### User Story 1 - User Authentication
1. Given user is on signup page, When user enters valid email/password/name and submits, Then account created and redirected to dashboard
2. Given user has account, When user enters correct email/password on signin and submits, Then authenticated and redirected to dashboard
3. Given user is authenticated, When user clicks sign out, Then session terminated and redirected to login

### User Story 2 - Basic Task Management
1. Given user authenticated on dashboard, When user enters task title and submits, Then new task appears in list with defaults
2. Given user has tasks, When user marks task complete, Then status updates and visually distinct
3. Given user has task, When user deletes with confirmation, Then task removed from list

### User Story 3 - Task Organization
1. Given user has multiple tasks with different statuses, When user applies status filter, Then only matching tasks displayed
2. Given user has multiple tasks, When user enters search text, Then only tasks containing text in title/description displayed
3. Given user has multiple tasks, When user selects sort option, Then tasks reordered by criteria

### User Story 4 - Responsive Design/UX
1. Given user on any device, When user toggles dark mode, Then color scheme changes appropriately
2. Given user interacting, When API calls in progress, Then loading indicators displayed
3. Given user on mobile, When user navigates, Then interface adapts to smaller screen

### User Story 5 - Advanced Features
1. Given user has tasks, When user exports, Then file (CSV/JSON) downloaded with all task data
2. Given user has multiple tasks, When user drags task to new position, Then list reordered accordingly
3. Given user performs action, When user triggers undo, Then previous action reversed

### Edge Cases
- Given user's internet connection is lost, When using application offline, Then appropriate offline indicators shown and sync occurs when connection restored
- Given user enters invalid input in forms, When submitting, Then validation errors displayed with clear guidance
- Given user tries to access dashboard without authentication, When navigating to protected route, Then redirected to login page
- Given user has large number of tasks (>1000), When viewing dashboard, Then pagination or virtual scrolling prevents performance issues
- Given user tries to create task with invalid due date, When submitting, Then appropriate error message shown
- Given user's JWT token expires during session, When making API request, Then automatically redirected to login with clear message

---

### Acceptance Scenario Test Cases

**Test Case US1-1**: Given user is on signup page, When user enters valid email/password/name and submits, Then account created and redirected to dashboard
**Test Case US1-2**: Given user has account, When user enters correct email/password on signin and submits, Then authenticated and redirected to dashboard
**Test Case US1-3**: Given user is authenticated, When user clicks sign out, Then session terminated and redirected to login

**Test Case US2-1**: Given user authenticated on dashboard, When user enters task title and submits, Then new task appears in list with defaults
**Test Case US2-2**: Given user has tasks, When user marks task complete, Then status updates and visually distinct
**Test Case US2-3**: Given user has task, When user deletes with confirmation, Then task removed from list

**Test Case US3-1**: Given user has multiple tasks with different statuses, When user applies status filter, Then only matching tasks displayed
**Test Case US3-2**: Given user has multiple tasks, When user enters search text, Then only tasks containing text in title/description displayed
**Test Case US3-3**: Given user has multiple tasks, When user selects sort option, Then tasks reordered by criteria

**Test Case US4-1**: Given user on any device, When user toggles dark mode, Then application color scheme changes appropriately
**Test Case US4-2**: Given user interacting, When API calls in progress, Then loading indicators displayed
**Test Case US4-3**: Given user on mobile, When user navigates, Then interface adapts to smaller screen

**Test Case US5-1**: Given user has tasks, When user exports tasks, Then file (CSV/JSON) downloaded with all task data
**Test Case US5-2**: Given user has multiple tasks, When user drags task to new position, Then task list reordered accordingly
**Test Case US5-3**: Given user performs action, When user triggers undo, Then previous action reversed

**Test Case EDGE-1**: Given user's internet connection is lost, When using application offline, Then appropriate offline indicators shown and sync occurs when connection restored
**Test Case EDGE-2**: Given user enters invalid input in forms, When submitting, Then validation errors displayed with clear guidance
**Test Case EDGE-3**: Given user tries to access dashboard without authentication, When navigating to protected route, Then redirected to login page
**Test Case EDGE-4**: Given user has large number of tasks (>1000), When viewing dashboard, Then pagination or virtual scrolling prevents performance issues
**Test Case EDGE-5**: Given user tries to create task with invalid due date, When submitting, Then appropriate error message shown
**Test Case EDGE-6**: Given user's JWT token expires during session, When making API request, Then automatically redirected to login with clear message

## Implementation Details

### Environment Variables
- `NEXT_PUBLIC_API_URL` - Backend API base URL (e.g., http://localhost:8000 for development)
- `NEXT_PUBLIC_BETTER_AUTH_URL` - Better Auth base URL
- `BETTER_AUTH_SECRET` - Shared secret for JWT signing/verification (same as backend)

### Error Handling
- **Error Boundaries**: Global error boundary component in root layout
- **Error Types**: Network errors, validation errors, authentication errors, server errors
- **User-Friendly Messages**: Clear, actionable error messages with suggestions
- **Logging**: Client-side error logging with sanitized messages

### Loading States
- **LoadingSpinner Component**: Reusable spinner with accessibility labels
- **Skeleton Screens**: Placeholder UI for content loading
- **Progressive Loading**: Show available data while loading additional content
- **API Loading States**: Visual indicators during API calls

### Form Validation
- **React Hook Form**: With Zod schema validation
- **Validation Rules**: Required fields, character limits, email format, password strength
- **Error Display**: Inline error messages with visual indicators
- **Accessibility**: ARIA attributes for screen readers

### Responsive Design
- **Breakpoints**: Mobile: <640px, Tablet: 640-1024px, Desktop: >1024px
- **Tailwind Classes**: Responsive utility classes for different screen sizes
- **Touch Targets**: Adequate touch targets for mobile (min 44px)
- **Flexible Layouts**: Grid and flexbox layouts that adapt to screen size

### Dark Mode
- **Implementation**: Using next-themes for theme management
- **Persistence**: Theme preference saved to localStorage
- **Accessibility**: Proper contrast ratios in both themes
- **System Preference**: Respects user's system theme preference

### Keyboard Shortcuts
- **Library Choice**: react-hotkeys-hook for keyboard management
- **Shortcuts Defined**: Ctrl+K (search), Ctrl+N (new task), Delete (delete task), etc.
- **Accessibility**: Visible shortcut hints and focus indicators
- **Conflicts**: Proper scope management to avoid conflicts

### Drag & Drop
- **Library Choice**: @dnd-kit/core for drag-and-drop functionality
- **Implementation**: Vertical list reordering with smooth animations
- **Accessibility**: Keyboard-accessible drag handles and reordering
- **Performance**: Optimized for large lists with virtual scrolling

### Undo/Redo
- **State Management**: useReducer with history pattern for state tracking
- **Implementation**: Command pattern for reversible operations
- **UI**: Toast notification with undo option
- **Duration**: 5-second undo window by default

### Real-time Updates
- **Polling Interval**: 5-second intervals for task list updates
- **WebSocket Upgrade Path**: Future-ready for WebSocket implementation
- **Efficiency**: Smart polling with conditional requests
- **User Feedback**: Visual indicators for updates

### Service Workers
- **Caching Strategy**: Cache-First for static assets, Network-First for API calls
- **Offline Queue**: Store operations locally for sync when online
- **Updates**: Versioned caching with automatic updates
- **Install**: Prompts users to install as PWA

### Build/Deployment
- **Commands**: `npm run build` for production build, `npm start` for production server
- **Dockerfile**: Optional Docker configuration for containerized deployment
- **Deployment Targets**: Vercel, Netlify, or self-hosted Node.js server
- **Optimization**: Bundle analysis and code splitting

### CI/CD Pipeline
- **GitHub Actions**: Workflow for `phase_2` branch
- **Test Steps**: Run unit tests, integration tests, accessibility tests
- **Lint Steps**: TypeScript checking, ESLint, Prettier formatting
- **Build Steps**: Production build with size analysis
- **Deployment**: Conditional deployment based on test results

## Testing Strategy

### Unit Tests
- **Framework**: React Testing Library with Jest
- **Coverage**: Component rendering, prop handling, event handling
- **Focus**: Isolated component behavior and business logic

### Integration Tests
- **Framework**: React Testing Library with user-event
- **Coverage**: Component interactions, API client integration
- **Focus**: Component combinations and data flow

### E2E Tests
- **Framework**: Playwright for critical user flows
- **Coverage**: Authentication flow, task CRUD operations, export/import
- **Focus**: End-to-end user journeys and cross-component interactions

### Accessibility Tests
- **Framework**: axe-core for automated accessibility testing
- **Coverage**: WCAG 2.1 AA compliance validation
- **Focus**: Keyboard navigation, screen reader compatibility, color contrast

### Performance Tests
- **Framework**: Lighthouse CI for performance monitoring
- **Coverage**: Bundle size, loading times, runtime performance
- **Focus**: Performance regression detection

## Project Structure

### Documentation (this feature)

```text
specs/002-frontend-todo-app/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
frontend/
├── app/
│   ├── signup/
│   │   └── page.tsx
│   ├── signin/
│   │   └── page.tsx
│   ├── dashboard/
│   │   └── page.tsx
│   ├── tasks/
│   │   └── [id]/
│   │       └── page.tsx
│   └── layout.tsx
├── components/
│   ├── TaskList.tsx
│   ├── TaskItem.tsx
│   ├── TaskForm.tsx
│   ├── FilterControls.tsx
│   ├── SortControls.tsx
│   ├── SearchBar.tsx
│   ├── BulkActions.tsx
│   ├── PaginationControls.tsx
│   ├── TaskStatistics.tsx
│   ├── TaskDetailModal.tsx
│   ├── ExportImportControls.tsx
│   ├── DarkModeToggle.tsx
│   ├── KeyboardShortcuts.tsx
│   ├── LoadingSpinner.tsx
│   ├── ToastNotification.tsx
│   └── ProtectedRoute.tsx
├── lib/
│   ├── api.ts
│   └── utils.ts
├── types/
│   └── index.ts
├── hooks/
│   └── index.ts
└── styles/
    └── globals.css
```

**Structure Decision**: Web application frontend structure selected with `/frontend` directory containing Next.js App Router pages in `/app`, reusable components in `/components`, centralized API client in `/lib/api.ts`, TypeScript types in `/types`, and custom hooks in `/hooks` as specified in the constitution and feature spec.

## Data Model and Database Considerations

### Task Data Structure
The frontend application works with tasks that have the following structure (as defined by backend database model):
- **Task Entity**: Tasks in the database include: `id` (integer, primary key, auto-increment), `user_id` (string, foreign key to users table, UUID), `title` (string, required, max 200 characters), `description` (text, optional, max 1000 characters), `completed` (boolean, default false), `priority` (enum: 'low'|'medium'|'high'), `due_date` (string, optional), `tags` (string array), `created_at` (timestamp), `updated_at` (timestamp).

### Database Indexing
While the frontend doesn't directly handle database indexing, it relies on the backend implementing these indexes for optimal performance:
- Database indexes MUST be created: tasks.user_id (for filtering by user), tasks.completed (for status filtering), users.email (unique index)

### Type Safety and Validation
- The frontend implements TypeScript interfaces that align with the backend database schema
- Client-side validation complements backend validation for better UX
- All API responses are validated against TypeScript interfaces

## Conflict Resolution Strategy

### Offline Data Synchronization
- **Strategy**: Queue operations locally when offline, sync when connection restored
- **Implementation**: Service workers intercept API requests and store in IndexedDB queue
- **Conflict Detection**: Compare timestamps (server vs client) to detect conflicts
- **Resolution Rule**: Server wins for timestamp-based conflicts; client wins for newer operations
- **User Feedback**: Visual indicators for offline status and sync status
- **Error Handling**: Retry failed sync attempts with exponential backoff

### Concurrent Edit Resolution
- **Strategy**: Last-write-wins with user notification
- **Implementation**: Include version/etag in API responses and requests
- **Conflict Detection**: Compare version numbers before updating
- **User Notification**: Alert user if task was modified by another session
- **Resolution Options**: Allow user to override or refresh from server

## Implementation Details

### Environment Variables
- `NEXT_PUBLIC_API_URL` - Backend API base URL (e.g., http://localhost:8000 for development)
- `NEXT_PUBLIC_BETTER_AUTH_URL` - Better Auth base URL
- `BETTER_AUTH_SECRET` - Shared secret for JWT signing/verification (same as backend)
- `NEXT_PUBLIC_API_URL` - Base URL for API calls

### Error Handling
- **Error Boundaries**: Global error boundary component in root layout
- **Error Types**: Network errors, validation errors, authentication errors, server errors
- **User-Friendly Messages**: Clear, actionable error messages with suggestions
- **Logging**: Client-side error logging with sanitized messages
- **API Error Responses**: Consistent format with error code, message, and details

### Loading States
- **LoadingSpinner Component**: Reusable spinner with accessibility labels
- **Skeleton Screens**: Placeholder UI for content loading
- **Progressive Loading**: Show available data while loading additional content
- **API Loading States**: Visual indicators during API calls

### Form Validation
- **React Hook Form**: With Zod schema validation
- **Validation Rules**: Required fields, character limits, email format, password strength
- **Error Display**: Inline error messages with visual indicators
- **Accessibility**: ARIA attributes for screen readers

### Responsive Design
- **Breakpoints**: Mobile: <640px, Tablet: 640-1024px, Desktop: >1024px
- **Tailwind Classes**: Responsive utility classes for different screen sizes
- **Touch Targets**: Adequate touch targets for mobile (min 44px)
- **Flexible Layouts**: Grid and flexbox layouts that adapt to screen size

### Dark Mode
- **Implementation**: Using next-themes for theme management
- **Persistence**: Theme preference saved to localStorage
- **Accessibility**: Proper contrast ratios in both themes
- **System Preference**: Respects user's system theme preference

### Keyboard Shortcuts
- **Library Choice**: react-hotkeys-hook for keyboard management
- **Shortcuts Defined**: Ctrl+K (search), Ctrl+N (new task), Delete (delete task), etc.
- **Accessibility**: Visible shortcut hints and focus indicators
- **Conflicts**: Proper scope management to avoid conflicts

### Drag & Drop
- **Library Choice**: @dnd-kit/core for drag-and-drop functionality
- **Implementation**: Vertical list reordering with smooth animations
- **Accessibility**: Keyboard-accessible drag handles and reordering
- **Performance**: Optimized for large lists with virtual scrolling

### Undo/Redo
- **State Management**: useReducer with history pattern for state tracking
- **Implementation**: Command pattern for reversible operations
- **UI**: Toast notification with undo option
- **Duration**: 5-second undo window by default

### Real-time Updates
- **Polling Interval**: 5-second intervals for task list updates
- **WebSocket Upgrade Path**: Future-ready for WebSocket implementation
- **Efficiency**: Smart polling with conditional requests
- **User Feedback**: Visual indicators for updates

### Service Workers
- **Caching Strategy**: Cache-First for static assets, Network-First for API calls
- **Offline Queue**: Store operations locally for sync when online
- **Updates**: Versioned caching with automatic updates
- **Install**: Prompts users to install as PWA

### Build/Deployment
- **Commands**: `npm run build` for production build, `npm start` for production server
- **Dockerfile**: Optional Docker configuration for containerized deployment
- **Deployment Targets**: Vercel, Netlify, or self-hosted Node.js server
- **Optimization**: Bundle analysis and code splitting

### CI/CD Pipeline
- **GitHub Actions**: Workflow for `phase_2` branch
- **Test Steps**: Run unit tests, integration tests, accessibility tests
- **Lint Steps**: TypeScript checking, ESLint, Prettier formatting
- **Build Steps**: Production build with size analysis
- **Deployment**: Conditional deployment based on test results

## Testing Strategy

### Unit Tests
- **Framework**: React Testing Library with Jest
- **Coverage**: Component rendering, prop handling, event handling
- **Focus**: Isolated component behavior and business logic

### Integration Tests
- **Framework**: React Testing Library with user-event
- **Coverage**: Component interactions, API client integration
- **Focus**: Component combinations and data flow

### E2E Tests
- **Framework**: Playwright for critical user flows
- **Coverage**: Authentication flow, task CRUD operations, export/import
- **Focus**: End-to-end user journeys and cross-component interactions

### Accessibility Tests
- **Framework**: axe-core for automated accessibility testing
- **Coverage**: WCAG 2.1 AA compliance validation
- **Focus**: Keyboard navigation, screen reader compatibility, color contrast

### Performance Tests
- **Framework**: Lighthouse CI for performance monitoring
- **Coverage**: Bundle size, loading times, runtime performance
- **Focus**: Performance regression detection

## Project Structure

### Documentation (this feature)

```text
specs/002-frontend-todo-app/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
frontend/
├── app/
│   ├── signup/
│   │   └── page.tsx
│   ├── signin/
│   │   └── page.tsx
│   ├── dashboard/
│   │   └── page.tsx
│   ├── tasks/
│   │   └── [id]/
│   │       └── page.tsx
│   └── layout.tsx
├── components/
│   ├── TaskList.tsx
│   ├── TaskItem.tsx
│   ├── TaskForm.tsx
│   ├── FilterControls.tsx
│   ├── SortControls.tsx
│   ├── SearchBar.tsx
│   ├── BulkActions.tsx
│   ├── PaginationControls.tsx
│   ├── TaskStatistics.tsx
│   ├── TaskDetailModal.tsx
│   ├── ExportImportControls.tsx
│   ├── DarkModeToggle.tsx
│   ├── KeyboardShortcuts.tsx
│   ├── LoadingSpinner.tsx
│   ├── ToastNotification.tsx
│   └── ProtectedRoute.tsx
├── lib/
│   ├── api.ts
│   └── utils.ts
├── types/
│   └── index.ts
├── hooks/
│   └── index.ts
└── styles/
    └── globals.css
```

**Structure Decision**: Web application frontend structure selected with `/frontend` directory containing Next.js App Router pages in `/app`, reusable components in `/components`, centralized API client in `/lib/api.ts`, TypeScript types in `/types`, and custom hooks in `/hooks` as specified in the constitution and feature spec.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
