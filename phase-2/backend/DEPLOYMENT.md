# Backend Deployment Guide

This document provides comprehensive instructions for deploying the FastAPI Todo backend to various environments.

## Table of Contents

- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Database Migrations](#database-migrations)
- [Docker Deployment](#docker-deployment)
- [Production Configuration](#production-configuration)
- [Monitoring Setup](#monitoring-setup)
- [Troubleshooting](#troubleshooting)

---

## Environment Variables

### Required Environment Variables

All environments (development, staging, production) require these variables:

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@host:port/database_name
# Example: postgresql://user:pass@neon.tech:5432/todo_db

# Authentication
BETTER_AUTH_SECRET=your-secret-key-minimum-32-characters
# Generate with: openssl rand -hex 32

# Environment
ENVIRONMENT=development|staging|production
```

### Optional Environment Variables

```bash
# CORS Configuration
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
# Comma-separated list of allowed origins

# Logging
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
# Default: INFO

# Server Configuration
PORT=8000
# Default: 8000

# Request Timeout
REQUEST_TIMEOUT=30
# Default: 30 seconds

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
# Default: 60 requests per minute
```

### Environment Variable File

Create a `.env` file in the `phase-2/backend/` directory:

```bash
# .env file (DO NOT commit to version control)
DATABASE_URL=postgresql://user:password@localhost:5432/todo_db
BETTER_AUTH_SECRET=your-secret-key-here
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
```

### Production Environment Variables

For production, use a secure secrets management system (AWS Secrets Manager, HashiCorp Vault, etc.):

```bash
# Production .env (stored in secrets manager)
DATABASE_URL=postgresql://prod_user:secure_password@neon.tech:5432/todo_prod
BETTER_AUTH_SECRET=<64-character-random-string>
ENVIRONMENT=production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
LOG_LEVEL=WARNING
PORT=8000
REQUEST_TIMEOUT=30
```

---

## Database Setup

### Neon Serverless PostgreSQL

1. **Create Neon Account**: Sign up at [neon.tech](https://neon.tech)

2. **Create Database**:
   ```bash
   # Via Neon Console:
   # - Create new project
   # - Note the connection string
   # - Enable connection pooling (recommended)
   ```

3. **Connection Pooling** (Recommended):
   ```
   postgresql://user:password@host:5432/dbname?sslmode=require&pgbouncer=true
   ```

### Local PostgreSQL (Development)

```bash
# Install PostgreSQL
brew install postgresql@16  # macOS
sudo apt install postgresql-16  # Ubuntu

# Start PostgreSQL
brew services start postgresql@16  # macOS
sudo systemctl start postgresql  # Ubuntu

# Create database
createdb todo_dev

# Connection string
DATABASE_URL=postgresql://localhost:5432/todo_dev
```

---

## Database Migrations

### Running Migrations

```bash
# Navigate to backend directory
cd phase-2/backend

# Run migrations
uv run alembic upgrade head
```

### Creating New Migrations

```bash
# Auto-generate migration from model changes
uv run alembic revision --autogenerate -m "Description of changes"

# Review the generated migration file in alembic/versions/

# Apply the migration
uv run alembic upgrade head
```

### Rollback Migrations

```bash
# Rollback one migration
uv run alembic downgrade -1

# Rollback to specific revision
uv run alembic downgrade <revision_id>

# Rollback all migrations
uv run alembic downgrade base
```

### Migration Best Practices

1. **Always review auto-generated migrations** before applying
2. **Test migrations on staging** before production
3. **Create backup** before running migrations in production
4. **Use transactions** for data migrations
5. **Never modify applied migrations** - create new ones instead

---

## Docker Deployment

### Build Docker Image

```bash
# Navigate to backend directory
cd phase-2/backend

# Build production image
docker build -t todo-backend:latest .

# Build with version tag
docker build -t todo-backend:1.0.0 .
```

### Run Docker Container

```bash
# Run with environment variables
docker run -d \
  --name todo-backend \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e BETTER_AUTH_SECRET="your-secret-key" \
  -e ENVIRONMENT="production" \
  -e CORS_ORIGINS="https://yourdomain.com" \
  todo-backend:latest

# Check logs
docker logs -f todo-backend

# Check health
curl http://localhost:8000/health
```

### Docker Compose (with PostgreSQL)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: todo_user
      POSTGRES_PASSWORD: todo_password
      POSTGRES_DB: todo_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U todo_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://todo_user:todo_password@postgres:5432/todo_db
      BETTER_AUTH_SECRET: ${BETTER_AUTH_SECRET}
      ENVIRONMENT: production
      CORS_ORIGINS: ${CORS_ORIGINS}
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
```

Run with Docker Compose:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

---

## Production Configuration

### Uvicorn Production Settings

The Dockerfile includes optimized production settings:

```bash
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \              # Multi-process workers
  --log-level info \         # Appropriate logging
  --access-log \             # Enable access logs
  --no-access-log            # Or disable for performance
```

### Worker Configuration

Calculate optimal workers:

```
workers = (2 x CPU_cores) + 1
```

For 2 CPU cores: 5 workers
For 4 CPU cores: 9 workers

### Reverse Proxy (Nginx)

Recommended Nginx configuration:

```nginx
upstream todo_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    # SSL configuration
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://todo_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://todo_backend/health;
        access_log off;
    }
}
```

### Cloud Deployment Platforms

#### AWS (Elastic Beanstalk)

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p docker todo-backend

# Create environment
eb create production

# Deploy
eb deploy
```

#### Google Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/todo-backend

# Deploy
gcloud run deploy todo-backend \
  --image gcr.io/PROJECT_ID/todo-backend \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL="..." \
  --set-env-vars BETTER_AUTH_SECRET="..."
```

#### Heroku

```bash
# Login to Heroku
heroku login

# Create app
heroku create todo-backend-prod

# Set environment variables
heroku config:set DATABASE_URL="postgresql://..."
heroku config:set BETTER_AUTH_SECRET="..."

# Deploy
git push heroku main
```

---

## Monitoring Setup

### Health Checks

The application provides health check endpoints:

```bash
# Basic health check
curl http://localhost:8000/health

# API health check
curl http://localhost:8000/api/health
```

### Logging

Logs are output to stdout/stderr. Configure log aggregation:

**CloudWatch (AWS)**:
```bash
# Install CloudWatch agent
# Configure log groups
# Ship container logs to CloudWatch
```

**Stackdriver (GCP)**:
```bash
# Automatic logging in Google Cloud Run
# View logs in Cloud Console
```

### Application Metrics

Monitor these key metrics:

1. **Request Rate**: Requests per second
2. **Response Time**: p50, p95, p99 latencies
3. **Error Rate**: 4xx and 5xx responses
4. **Database Connections**: Active connections, connection pool usage
5. **Memory Usage**: Container memory utilization
6. **CPU Usage**: Container CPU utilization

### Prometheus Integration

See `monitoring/prometheus.yml` for Prometheus configuration.

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

**Error**: `connection to server at "host" failed`

**Solutions**:
- Verify DATABASE_URL is correct
- Check firewall rules allow database access
- Ensure database is running and accessible
- Verify SSL/TLS settings (`sslmode=require`)

```bash
# Test database connection
psql "$DATABASE_URL"

# Check if database is reachable
nc -zv database-host 5432
```

#### 2. JWT Token Errors

**Error**: `Invalid token` or `Token expired`

**Solutions**:
- Verify BETTER_AUTH_SECRET matches frontend
- Check token expiration time (7 days default)
- Ensure JWT middleware is configured correctly

```bash
# Verify secret is set
echo $BETTER_AUTH_SECRET

# Generate new secret if needed
openssl rand -hex 32
```

#### 3. CORS Errors

**Error**: `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solutions**:
- Add frontend domain to CORS_ORIGINS
- Ensure protocol (http/https) matches
- Check for trailing slashes

```bash
# Correct format
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Incorrect format (missing comma)
CORS_ORIGINS=http://localhost:3000 https://yourdomain.com
```

#### 4. Migration Errors

**Error**: `Target database is not up to date`

**Solutions**:
```bash
# Check current migration status
uv run alembic current

# Check migration history
uv run alembic history

# Upgrade to latest
uv run alembic upgrade head

# If stuck, stamp the database
uv run alembic stamp head
```

#### 5. Docker Build Failures

**Error**: `failed to solve with frontend dockerfile.v0`

**Solutions**:
```bash
# Clear Docker build cache
docker builder prune

# Build with no cache
docker build --no-cache -t todo-backend:latest .

# Check Dockerfile syntax
docker build -t todo-backend:latest . --progress=plain
```

### Performance Issues

#### Slow Database Queries

```bash
# Enable query logging in PostgreSQL
ALTER DATABASE todo_db SET log_min_duration_statement = 1000;

# Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

#### High Memory Usage

```bash
# Check container memory
docker stats todo-backend

# Reduce workers if memory constrained
uvicorn main:app --workers 2

# Monitor memory in application
# Add memory profiling middleware
```

### Getting Help

1. **Check Logs**: Always start with application and database logs
2. **Review Documentation**: Check FastAPI, SQLModel, and Neon docs
3. **GitHub Issues**: Search for similar issues in repository
4. **Contact Support**: Reach out to team for assistance

---

## Security Checklist

Before deploying to production:

- [ ] Environment variables stored securely (not in code)
- [ ] BETTER_AUTH_SECRET is strong (64+ characters)
- [ ] DATABASE_URL uses SSL/TLS (`sslmode=require`)
- [ ] CORS_ORIGINS restricted to known domains
- [ ] Docker image runs as non-root user
- [ ] Security headers configured (via Nginx or middleware)
- [ ] Rate limiting enabled
- [ ] Database backups configured
- [ ] Monitoring and alerting configured
- [ ] SSL/TLS certificates valid and not expiring soon

---

## Deployment Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Docker image built and tested
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Logs aggregation configured
- [ ] Backup strategy in place
- [ ] Rollback plan documented
- [ ] Load testing completed
- [ ] Security scan passed

---

## Support

For deployment assistance:
- **Documentation**: Check `/docs` and `/redoc` endpoints
- **Issues**: Create GitHub issue with deployment logs
- **Team**: Contact backend team via Slack/Email
