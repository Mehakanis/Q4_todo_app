# Quickstart Guide: Frontend Todo Application

## Prerequisites
- Node.js 18+ installed
- npm or pnpm package manager
- Backend API running (typically on http://localhost:8000)

## Setup Instructions

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd frontend
```

### 2. Install Dependencies
```bash
npm install
# OR
pnpm install
```

### 3. Environment Configuration
Create `.env.local` file in the frontend root:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_BETTER_AUTH_URL=http://localhost:3000
BETTER_AUTH_SECRET=your-secret-key
```

### 4. Run Development Server
```bash
npm run dev
# OR
pnpm dev
```

Application will be available at http://localhost:3000

## Key Features Overview

### Authentication Flow
1. User visits `/signup` to create account
2. User visits `/signin` to log in
3. JWT token is stored and automatically attached to API requests
4. Protected routes redirect to login if unauthenticated

### Task Management
1. Access `/dashboard` after authentication
2. Create tasks using the form
3. View tasks in the list
4. Filter, sort, and search tasks
5. Update or delete tasks as needed

### API Client Usage
```typescript
// Example usage in components
import { api } from '@/lib/api';

// Get user's tasks
const tasks = await api.getTasks(userId, { status: 'pending', sort: 'created' });

// Create a new task
const newTask = await api.createTask(userId, { title: 'New Task', priority: 'high' });
```

## Component Structure
- Pages: Located in `/app` directory (Next.js App Router)
- Components: Located in `/components` directory (reusable UI elements)
- API Client: Located at `/lib/api.ts` (centralized API communication)
- Types: Located in `/types` directory (TypeScript definitions)

## Development Commands
```bash
# Development server
npm run dev

# Production build
npm run build

# Run tests
npm run test

# Type checking
npm run type-check

# Linting
npm run lint

# Formatting
npm run format
```

## Troubleshooting
- If authentication fails, ensure `BETTER_AUTH_SECRET` matches backend
- If API calls fail, verify `NEXT_PUBLIC_API_URL` points to running backend
- For styling issues, ensure Tailwind CSS is properly configured
- For server components not rendering, check Next.js App Router setup