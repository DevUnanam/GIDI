# GIDI Backend Phase 1

Production-ready Django REST backend foundation for the GIDI logistics platform.

## Project Structure

```text
.
├── accounts/
├── config/
├── deliveries/
├── notifications/
├── payments/
├── riders/
├── tracking/
├── wallets/
├── docker-compose.yml
├── Dockerfile
├── manage.py
└── requirements.txt
```

## Run Locally

```bash
cp .env.example .env
docker compose up --build
```

API schema is available at `/api/schema/`, Swagger UI at `/api/docs/`, and Redoc at `/api/redoc/`.
