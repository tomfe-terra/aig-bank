# AIG UI

Main banking interface for the AIG Bank platform.

## Tech Stack

- Vue 3
- Vuetify 3
- TypeScript
- Vite
- Vue Router
- TanStack Query

## Development

```bash
npm install
npm run dev
```

Runs on `http://localhost:5173`

## Production

```bash
npm run build
npm run preview
```

## Environment Variables

- `VITE_API_BASE_URL` - Optional backend API base URL override
- If `VITE_API_BASE_URL` is not set, the app derives the API URL from the browser location by replacing the `app` subdomain with `api` and using the `/api/v1` base path.

## Docker

```bash
docker build -t aig-ui .
docker run -p 80:80 aig-ui
```

