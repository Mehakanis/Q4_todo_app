# API Contracts: Frontend Todo Application

## Backend API Endpoints (Integration Contract)

### Authentication Endpoints
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

### Task Management Endpoints
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

## Frontend API Client Contract

### API Client Interface (`/lib/api.ts`)
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
```

### Request/Response Objects
```typescript
// Request objects
interface TaskCreationRequest {
  title: string;
  description?: string;
  priority?: 'low' | 'medium' | 'high';
  due_date?: string;
  tags?: string[];
}

interface TaskUpdateRequest {
  title?: string;
  description?: string;
  priority?: 'low' | 'medium' | 'high';
  due_date?: string;
  tags?: string[];
}

// Response objects
interface TaskResponse {
  id: number;
  user_id: string;
  title: string;
  description?: string;
  completed: boolean;
  priority: 'low' | 'medium' | 'high';
  due_date?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

interface UserResponse {
  id: string;
  email: string;
  name: string;
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

### Error Handling Contract
- All API methods return Promise<ApiResponse<T>>
- 401 errors trigger automatic redirect to login page
- Network errors are retried with exponential backoff
- Validation errors return appropriate error messages
- Rate limiting is handled with appropriate delays

### Authorization Contract
- JWT token is automatically attached to all requests
- Token is extracted from Better Auth session
- Token refresh happens automatically when needed
- Unauthorized requests (401) trigger logout and redirect to login