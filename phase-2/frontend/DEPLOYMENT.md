# Deployment Guide

This document provides comprehensive deployment instructions for the Frontend Todo Application across various platforms.

## Table of Contents

- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Vercel Deployment](#vercel-deployment)
- [Docker Deployment](#docker-deployment)
- [Self-Hosted Deployment](#self-hosted-deployment)
- [Environment Configuration](#environment-configuration)
- [Post-Deployment Verification](#post-deployment-verification)
- [Troubleshooting](#troubleshooting)

## Pre-Deployment Checklist

Before deploying, ensure you have completed:

- [ ] All tests pass (`pnpm run test && pnpm run test:e2e`)
- [ ] TypeScript compilation successful (`pnpm exec tsc --noEmit`)
- [ ] ESLint checks pass (`pnpm run lint`)
- [ ] Production build successful (`pnpm run build`)
- [ ] Environment variables configured
- [ ] Backend API is accessible
- [ ] Security audit completed (`pnpm audit`)
- [ ] Lighthouse scores meet targets (>90 in all categories)
- [ ] Accessibility tests pass

## Vercel Deployment

### Method 1: Vercel CLI (Recommended)

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy to Staging**:
   ```bash
   cd phase-2/frontend
   vercel
   ```

4. **Deploy to Production**:
   ```bash
   vercel --prod
   ```

### Method 2: GitHub Integration

1. **Connect Repository**:
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "Add New Project"
   - Import your Git repository

2. **Configure Project**:
   - Framework Preset: `Next.js`
   - Root Directory: `phase-2/frontend`
   - Build Command: `pnpm run build`
   - Output Directory: `.next`

3. **Set Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com
   NEXT_PUBLIC_BETTER_AUTH_URL=https://yourdomain.com
   BETTER_AUTH_SECRET=<your-production-secret>
   ```

4. **Deploy**:
   - Click "Deploy"
   - Vercel will automatically deploy on every push to the main branch

### Vercel Configuration

Create `vercel.json` in the frontend directory:

```json
{
  "buildCommand": "pnpm run build",
  "devCommand": "pnpm run dev",
  "installCommand": "pnpm install",
  "framework": "nextjs",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://api.yourdomain.com/:path*"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        },
        {
          "key": "Referrer-Policy",
          "value": "strict-origin-when-cross-origin"
        }
      ]
    }
  ]
}
```

## Docker Deployment

### 1. Create Dockerfile

Create `Dockerfile` in the frontend directory:

```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml* ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set environment variables for build
ENV NEXT_TELEMETRY_DISABLED 1
ENV NODE_ENV production

# Build application
RUN npm install -g pnpm && pnpm run build

# Stage 3: Runner
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy necessary files
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
```

### 2. Create .dockerignore

```
node_modules
.next
.env*.local
npm-debug.log
README.md
.git
.gitignore
coverage
.vscode
```

### 3. Build and Run Docker Container

```bash
# Build image
docker build -t frontend-todo-app:latest .

# Run container (development)
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000 \
  -e NEXT_PUBLIC_BETTER_AUTH_URL=http://localhost:3000 \
  frontend-todo-app:latest

# Run container with env file (production)
docker run -p 3000:3000 --env-file .env.production frontend-todo-app:latest
```

### 4. Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
      - NEXT_PUBLIC_BETTER_AUTH_URL=${NEXT_PUBLIC_BETTER_AUTH_URL}
      - BETTER_AUTH_SECRET=${BETTER_AUTH_SECRET}
    restart: unless-stopped
    depends_on:
      - backend

  backend:
    image: backend-api:latest
    ports:
      - "8000:8000"
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

## Self-Hosted Deployment

### Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Node.js 20+
- Nginx (for reverse proxy)
- PM2 (for process management)
- SSL certificate (Let's Encrypt recommended)

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install pnpm
npm install -g pnpm

# Install PM2
npm install -g pm2

# Install Nginx
sudo apt install -y nginx
```

### 2. Deploy Application

```bash
# Clone repository
git clone <repository-url> /var/www/todo-app
cd /var/www/todo-app/phase-2/frontend

# Install dependencies
pnpm install --frozen-lockfile

# Create .env.production
cat > .env.production << EOF
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_BETTER_AUTH_URL=https://yourdomain.com
BETTER_AUTH_SECRET=<your-production-secret>
NODE_ENV=production
EOF

# Build application
pnpm run build

# Start with PM2
pm2 start "pnpm start" --name frontend-todo-app
pm2 save
pm2 startup
```

### 3. Configure Nginx

Create `/etc/nginx/sites-available/todo-app`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Proxy to Next.js
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Cache static assets
    location /_next/static {
        proxy_pass http://localhost:3000;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

Enable site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/todo-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Environment Configuration

### Staging Environment

`.env.staging`:
```bash
NEXT_PUBLIC_API_URL=https://api-staging.yourdomain.com
NEXT_PUBLIC_BETTER_AUTH_URL=https://staging.yourdomain.com
BETTER_AUTH_SECRET=<staging-secret>
NODE_ENV=production
```

### Production Environment

`.env.production`:
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_BETTER_AUTH_URL=https://yourdomain.com
BETTER_AUTH_SECRET=<production-secret>
NODE_ENV=production
```

## Post-Deployment Verification

### 1. Health Check

```bash
# Check if application is running
curl -f https://yourdomain.com || echo "Health check failed"

# Check API connectivity
curl -f https://yourdomain.com/api/health || echo "API check failed"
```

### 2. Performance Test

```bash
# Run Lighthouse
npx lighthouse https://yourdomain.com --output=html --output-path=./lighthouse-report.html

# Check Core Web Vitals
# Ensure LCP < 3s, FID < 100ms, CLS < 0.1
```

### 3. Security Test

```bash
# Check SSL
curl -I https://yourdomain.com | grep "Strict-Transport-Security"

# Run security scan
npm audit

# Check headers
curl -I https://yourdomain.com
```

### 4. Functional Test

Manual verification:
- [ ] User can sign up
- [ ] User can sign in
- [ ] Dashboard loads correctly
- [ ] Tasks can be created, edited, deleted
- [ ] Filtering and sorting work
- [ ] Search functionality works
- [ ] Dark mode toggle works
- [ ] Offline mode works (PWA)

## Troubleshooting

### Build Failures

**Issue**: Build fails with memory error
```bash
# Solution: Increase Node.js memory
NODE_OPTIONS="--max-old-space-size=4096" pnpm run build
```

**Issue**: TypeScript errors during build
```bash
# Solution: Check types
pnpm exec tsc --noEmit
```

### Runtime Errors

**Issue**: API connection failures
- Check `NEXT_PUBLIC_API_URL` is correct
- Verify backend is running and accessible
- Check CORS configuration on backend

**Issue**: Authentication errors
- Verify `BETTER_AUTH_SECRET` matches backend
- Check JWT token expiration
- Clear browser cookies and retry

### Performance Issues

**Issue**: Slow page loads
- Enable caching in Nginx
- Check bundle size: `pnpm run analyze`
- Optimize images
- Enable compression

**Issue**: High memory usage
- Restart PM2 process: `pm2 restart frontend-todo-app`
- Check for memory leaks in monitoring
- Scale horizontally if needed

### SSL Issues

**Issue**: Certificate errors
```bash
# Renew certificate
sudo certbot renew --force-renewal
sudo systemctl reload nginx
```

## Monitoring and Maintenance

### Application Monitoring

```bash
# View PM2 logs
pm2 logs frontend-todo-app

# Monitor process
pm2 monit

# View process status
pm2 status
```

### Nginx Logs

```bash
# Access logs
sudo tail -f /var/log/nginx/access.log

# Error logs
sudo tail -f /var/log/nginx/error.log
```

### Automated Backups

```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf /backups/frontend-$DATE.tar.gz /var/www/todo-app/phase-2/frontend

# Keep only last 7 backups
find /backups -name "frontend-*.tar.gz" -mtime +7 -delete
```

### Update Procedure

```bash
# Pull latest code
cd /var/www/todo-app
git pull origin main

# Install dependencies
cd phase-2/frontend
pnpm install --frozen-lockfile

# Build application
pnpm run build

# Restart PM2
pm2 restart frontend-todo-app

# Verify deployment
curl -f https://yourdomain.com || pm2 logs frontend-todo-app
```

## Rollback Procedure

```bash
# Revert to previous commit
git log --oneline  # Find previous stable commit
git checkout <commit-hash>

# Rebuild and restart
pnpm run build
pm2 restart frontend-todo-app
```

## Support

For deployment issues:
- Check logs: `pm2 logs frontend-todo-app`
- Review Nginx logs: `sudo tail -f /var/log/nginx/error.log`
- Verify environment variables
- Contact support: support@yourdomain.com
