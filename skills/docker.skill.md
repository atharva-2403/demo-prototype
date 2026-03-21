# Skill: Docker Compose Deployment
## Purpose
Patterns for multi-service Docker Compose configuration and production deployment.

## Key Knowledge

### docker-compose.yml Pattern
```yaml
version: '3.8'
services:
  backend:
    build: ./clearclaim-backend
    ports: ["8000:8000"]
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}   # From .env file at root
    volumes:
      - ./clearclaim-backend:/app                # Hot reload during dev

  frontend:
    build: ./clearclaim-frontend
    ports: ["3000:3000"]
    environment:
      - VITE_API_URL=http://localhost:8000/api
    depends_on: [backend]
```

### Backend Dockerfile Pattern
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv install --system --deploy
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile Pattern
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
RUN npm install -g serve
CMD ["serve", "-s", "dist", "-l", "3000"]
```

### Production Deployment
Frontend → Vercel: add VITE_API_URL environment variable pointing to Render backend URL.
Backend → Render: add ANTHROPIC_API_KEY in Render dashboard environment variables.
Run `docker-compose up` locally to verify both services connect before deploying.

## MUST_NOT
- MUST_NOT commit .env files to Git — add to .gitignore before anything else.
- MUST_NOT hardcode ANTHROPIC_API_KEY in any Dockerfile or docker-compose.yml.
- MUST_NOT forget `depends_on: [backend]` — frontend starts before backend without it.

## Discovered During Implementation
