# Todo Console Application

A comprehensive todo application project showcasing the evolution from a simple CLI application to a full-stack web application with Kubernetes deployment.

## Project Overview

This repository contains the complete evolution of a todo application, progressing through multiple phases:

- **Phase 1**: CLI Todo Application (Python + Click framework)
- **Phase 2**: Full-Stack Web Application (Next.js + FastAPI) ✅ **COMPLETED**
- **Phase 3**: AI-Powered Chatbot (OpenAI ChatKit + Agents SDK) ✅ **COMPLETED**
- **Phase 4**: Kubernetes Deployment (Minikube + Helm) 🚧 **IN PROGRESS**

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

## Phase 4: Kubernetes Deployment 🚧

**Status: IN PROGRESS** - Deploy the application to a local Minikube Kubernetes cluster using Helm charts.

### Prerequisites

- Minikube 1.32+
- Helm 3.x
- Docker 24+
- kubectl

### One-Command Deployment

The easiest way to deploy is using the automated deployment script:

**Linux/macOS (Bash):**
```bash
# Set required environment variables in phase-4/backend/.env:
# - DATABASE_URL
# - BETTER_AUTH_SECRET
# - OPENAI_API_KEY (or OPENROUTER_API_KEY/GEMINI_API_KEY based on LLM_PROVIDER)

# Run the deployment script
./scripts/deploy.sh
```

**Windows (PowerShell):**
```powershell
# Run the deployment script
.\scripts\deploy.ps1
```

The deployment script automatically:
1. Validates prerequisites (minikube, helm, docker, kubectl)
2. Starts Minikube if not running
3. Configures Docker to use Minikube's daemon
4. Builds Docker images in Minikube context
5. Loads environment variables from `.env` files
6. Installs/upgrades Helm chart with secrets
7. Waits for pods to be ready
8. Displays access URLs

**Expected completion time**: Under 10 minutes on first run, faster on subsequent runs.

### Manual Deployment

If you prefer manual control:

```bash
# Start Minikube
minikube start

# Configure Docker to use Minikube's daemon
eval $(minikube docker-env)

# Build images
docker build -t todo-frontend:latest ./phase-4/frontend
docker build -t todo-backend:latest ./phase-4/backend

# Deploy using Helm
helm upgrade --install todo-app ./k8s/todo-app \
  --create-namespace \
  --namespace todo \
  --set secrets.databaseUrl="your-database-url" \
  --set secrets.betterAuthSecret="your-auth-secret" \
  --set secrets.openaiApiKey="your-openai-key"

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=todo-app -n todo --timeout=120s

# Access the application
echo "Frontend: http://$(minikube ip):30300"
```

### Required Environment Variables

Create a `.env` file in `phase-4/backend/` with:

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
BETTER_AUTH_SECRET=your-secret-key
OPENAI_API_KEY=your-openai-api-key
LLM_PROVIDER=openai  # or: openrouter, gemini
```

### Horizontal Scaling

Scale deployments as needed:

```bash
# Scale frontend to 3 replicas
kubectl scale deployment todo-frontend --replicas=3 -n todo

# Scale backend to 2 replicas
kubectl scale deployment todo-backend --replicas=2 -n todo
```

### Cleanup

To remove the deployment:

```bash
# Uninstall Helm release
helm uninstall todo-app -n todo

# Delete namespace
kubectl delete namespace todo

# Stop Minikube (optional)
minikube stop
```

### AI DevOps Tools

This project includes documentation for AI-powered DevOps tools that help developers understand and troubleshoot Kubernetes deployments:

- **kubectl-ai**: Natural language interface for kubectl commands
- **Kagent**: Kubernetes-native AI agent framework
- **Docker AI (Gordon)**: AI assistant built into Docker Desktop

See [AI DevOps Tools Guide](docs/ai-devops-tools.md) for installation, usage examples, and a troubleshooting cheat sheet.

### Kubernetes Resources

- **Helm Chart**: `k8s/todo-app/`
- **Frontend Service**: NodePort on port 30300
- **Backend Service**: ClusterIP on port 8000
- **ConfigMaps**: Non-sensitive configuration
- **Secrets**: Database credentials, API keys

### Health Checks

Both frontend and backend include health check endpoints:

- **Frontend**: `/api/health` (liveness), `/api/ready` (readiness)
- **Backend**: `/health` (liveness), `/ready` (readiness)

## Documentation

- [Backend README](phase-2/backend/README.md) - Complete backend documentation
- [Frontend README](phase-2/frontend/README.md) - Complete frontend documentation
- [AI DevOps Tools Guide](docs/ai-devops-tools.md) - AI-powered Kubernetes tools and troubleshooting

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
