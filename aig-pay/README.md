# AIG Pay

Payment gateway for the AIG Bank platform.

## Tech Stack

- Next.js 15
- React 19
- TypeScript
- Tailwind CSS

## Development

```bash
npm install
npm run dev
```

Runs on `http://localhost:3000`

## Production

```bash
npm run build
npm start
```

## Environment Variables

- `API_ENDPOINT` - Backend API URL
- `PORT` - Server port (default: 3000)
- `NODE_ENV` - Environment mode

## Docker

```bash
docker build -t aig-pay .
docker run -p 3000:3000 aig-pay
```

