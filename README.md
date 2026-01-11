# AIG Bank

A full-stack banking application with a modern web interface and payment processing system.

## Components

- **aig-bank-api** - FastAPI backend with PostgreSQL
- **aig-ui** - Vue 3 frontend (main banking interface)
- **aig-pay** - Next.js payment gateway
- **nginx** - Reverse proxy and SSL termination
- **postgres** - Database
- **pgweb** - Database viewer

Api Docs: https://api.aig-bank.int.terrasec.io/docs

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

