# Quickstart: Backend API Foundation

## Prerequisites

- Python 3.11+
- pip

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

## Run (mock mode, без БД)

```bash
USE_MOCK_DB=true uvicorn app.main:app --reload --port 8000
```

## Verify

```bash
# Health check
curl http://localhost:8000/api/v1/health

# List devices (mock data)
curl http://localhost:8000/api/v1/devices

# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"Test123!"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"Test123!"}'
```

## Run with real DB

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/greenhouse \
uvicorn app.main:app --reload --port 8000
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | `postgresql://localhost/greenhouse` | PostgreSQL connection string |
| USE_MOCK_DB | `false` | Use in-memory mocks instead of real DB |
| SECRET_KEY | `changeme` | JWT signing key |
| CORS_ORIGINS | `http://localhost:3000` | Allowed CORS origins (comma-separated) |
| ACCESS_TOKEN_EXPIRE_MINUTES | `60` | JWT token TTL |

## OpenAPI Docs

After starting the server:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
