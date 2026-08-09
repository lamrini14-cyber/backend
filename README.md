# SUNU YARAMA — Backend API

FastAPI + PostgreSQL + Alembic backend for [sunuyaram.shop](https://sunuyaram.shop).

## Local development

```bash
# 1. Copy env
cp .env.example .env
# Edit .env — set MAXMIND keys, CAPI tokens, SHEETS URL

# 2. Start with Docker Compose
docker compose up --build

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

## Manual setup (no Docker)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set DATABASE_URL to your local postgres
export DATABASE_URL=postgres://sunuyaram:sunuyaram@localhost:5432/sunuyaram

alembic upgrade head
uvicorn app.main:app --reload
```

## Key endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | App health |
| GET | `/health/db` | DB health |
| GET | `/api/v1/geo/check` | IP geo check |
| POST | `/api/v1/orders` | Create COD order |

## Test order (whitelist phone)

```bash
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Fatou Test",
    "phone": "0550000000",
    "locale": "fr",
    "items": [{"slug": "nuit-calm", "quantity": 1}],
    "tracking": {"event_id": "test-uuid-123", "user_agent": "TestAgent/1.0"}
  }'
```

## EasyPanel environment variables

See `.env.example` for the full list. Required for production:
- `DATABASE_URL`
- `MAXMIND_ACCOUNT_ID` + `MAXMIND_LICENSE_KEY`
- `META_PIXEL_ID` + `META_CAPI_ACCESS_TOKEN`
- `TIKTOK_PIXEL_ID` + `TIKTOK_ACCESS_TOKEN`
- `SNAP_PIXEL_ID` + `SNAP_CAPI_TOKEN`
- `GOOGLE_SHEETS_WEBHOOK_URL`
