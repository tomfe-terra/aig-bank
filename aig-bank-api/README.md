# AIG Bank API

FastAPI backend for the AIG Bank platform.

## Tech Stack

- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- Asyncpg
- Pydantic v2
- Python 3.14

## Development

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Runs on `http://localhost:8000`

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Secret key for JWT tokens
- `AES_KEY` - AES encryption key
- `HMAC_KEY` - HMAC signing key
- `CORS_ORIGINS` - Allowed CORS origins

## API Documentation

- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Docker

```bash
docker build -t aig-bank-api .
docker run -p 8000:8000 aig-bank-api
```

