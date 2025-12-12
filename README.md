# Todo Console Application

A comprehensive todo application project showcasing the evolution from a simple CLI application to a full-stack web application.

## Project Overview

This repository contains the complete evolution of a todo application, progressing through multiple phases:

- **Phase 1**: CLI Todo Application (Python + Click framework)
- **Phase 2**: Full-Stack Web Application (Next.js + FastAPI) ✅ **COMPLETED**

## Phase 2: Full-Stack Web Application ✅

**Status: COMPLETE** - Phase 2 includes a fully functional full-stack todo web application with modern features.

### Architecture

- **Frontend**: Next.js 16+ with TypeScript, Tailwind CSS, Better Auth
- **Backend**: FastAPI with PostgreSQL (Neon Serverless), Drizzle ORM, JWT authentication
- **Database**: PostgreSQL (Neon Serverless)
- **Authentication**: Better Auth with JWT tokens
- **Deployment**: Docker-ready, Vercel (frontend), GitHub Actions CI/CD

### Features

#### Frontend Features
- ✅ Modern UI with Shadcn UI components
- ✅ Framer Motion animations
- ✅ Dark/Light mode support
- ✅ Responsive design (mobile-first)
- ✅ Real-time task management
- ✅ Advanced filtering and sorting
- ✅ Search with debouncing
- ✅ Drag and drop task reordering
- ✅ Export/Import (CSV, JSON, PDF)
- ✅ PWA support (offline mode)
- ✅ Keyboard shortcuts
- ✅ Optimistic UI updates
- ✅ Toast notifications
- ✅ Loading states and error handling

#### Backend Features
- ✅ RESTful API with FastAPI
- ✅ JWT authentication with Better Auth
- ✅ PostgreSQL database with Drizzle ORM
- ✅ Task CRUD operations
- ✅ Advanced filtering and sorting
- ✅ Export/Import functionality
- ✅ PDF generation
- ✅ Rate limiting
- ✅ CORS configuration
- ✅ Comprehensive error handling
- ✅ Request logging
- ✅ Database migrations with Alembic

### Project Structure

```
todo_console/
├── phase-1/                    # CLI Todo Application
│   └── cli_todo_app/
│
└── phase-2/                    # Full-Stack Web Application ✅
    ├── frontend/               # Next.js frontend
    │   ├── app/               # Next.js App Router
    │   ├── components/        # React components
    │   ├── lib/               # Utilities and API client
    │   └── ...
    │
    └── backend/               # FastAPI backend
        ├── routes/            # API routes
        ├── services/          # Business logic
        ├── models/            # Database models
        ├── schemas/           # Pydantic schemas
        ├── utils/             # Utilities
        └── tests/             # Test suite
```

## Getting Started

### Prerequisites

- **For Phase 1**: Python 3.13+, UV package manager
- **For Phase 2**:
  - Node.js 20+ and pnpm 9+ (Frontend)
  - Python 3.13+ and UV (Backend)
  - PostgreSQL database (Neon Serverless recommended)

### Phase 2 Setup

#### Backend Setup

1. Navigate to backend directory:
```bash
cd phase-2/backend
```

2. Install dependencies:
```bash
uv sync
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run database migrations:
```bash
uv run alembic upgrade head
```

5. Start the backend server:
```bash
uv run uvicorn main:app --reload
```

Backend will run on `http://localhost:8000`

#### Frontend Setup

1. Navigate to frontend directory:
```bash
cd phase-2/frontend
```

2. Install dependencies:
```bash
pnpm install
```

3. Set up environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your configuration
```

4. Start the development server:
```bash
pnpm run dev
```

Frontend will run on `http://localhost:3000`

## Documentation

- [Backend README](phase-2/backend/README.md) - Complete backend documentation
- [Frontend README](phase-2/frontend/README.md) - Complete frontend documentation

## Environment Variables

⚠️ **Important**: All `.env` and `.env.local` files are gitignored to protect sensitive information.

### Backend Environment Variables
See [backend/.env.example](phase-2/backend/.env.example) for required variables.

### Frontend Environment Variables
See [frontend/.env.example](phase-2/frontend/.env.example) for required variables.

## Testing

### Backend Tests
```bash
cd phase-2/backend
uv run pytest
```

### Frontend Tests
```bash
cd phase-2/frontend
pnpm run test
```

## CI/CD

Both frontend and backend have GitHub Actions workflows configured:
- `.github/workflows/backend-ci.yml` - Backend CI/CD pipeline
- `.github/workflows/frontend-ci.yml` - Frontend CI/CD pipeline

## License

This project is part of a learning exercise and development showcase.
