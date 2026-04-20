# AIG Bank

A full-stack banking application with a modern web interface and payment processing system.

## Components

- **aig-bank-api** - FastAPI backend with PostgreSQL
- **aig-ui** - Vue 3 frontend (main banking interface)
- **aig-pay** - Next.js payment gateway
- **nginx** - Reverse proxy and SSL termination
- **postgres** - Database
- **pgweb** - Database viewer

Api Docs: [https://api.aig-bank.int.terrasec.io/docs](https://ubiquitous-broccoli-8ezq9qk.pages.github.io/docs/aig-bank/assets/endpoints/)

## Quick Start

1. Copy `env.example` to `.env` and configure environment variables
2. Start all services:
   ```bash
   docker-compose up -d
   ```

## Services

- Main UI: `https://app.{DOMAIN}`
- Payment Gateway: `https://pay.{DOMAIN}`
- API: `https://api.{DOMAIN}`
- API Docs: `https://api.{DOMAIN}/docs`

## Docker Images

GitHub Actions workflow: `.github/workflows/docker-build.yml`

Required repository variables:
- `AWS_REGION`
- `AWS_ROLE_ARN`
- `ECR_REPOSITORY_PREFIX`

The workflow builds amd64 images for:
- `aig-bank-api`
- `aig-ui`
- `aig-pay`

## Helm

Chart location: `helm/aig-bank`

The chart uses the Bitnami `postgresql` dependency chart for the database component.

Example install:
```bash
helm upgrade --install aig-bank ./helm/aig-bank \
  --set domain=bank.example.com \
  --set api.image.repository=<api-image> \
  --set ui.image.repository=<ui-image> \
  --set pay.image.repository=<pay-image>
```

`aig-ui` no longer requires a deployment-specific build arg for the API URL. If `VITE_API_BASE_URL` is not set at build time, the frontend falls back to the current browser host and swaps the `app` subdomain for `api`, using `/api/v1` as the API base path.

