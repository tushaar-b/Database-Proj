# IntelliVest investor workspace (React + Vite)

Responsive local dashboard for cash flow, affordable recommendations, portfolios, PostgreSQL risk metrics, and alerts. Financial results are read from FastAPI; the frontend does not connect directly to PostgreSQL.

## Local setup

1. Start the FastAPI backend and both PostgreSQL databases using the repository instructions.
2. Configure the local database URLs and password in the backend environment using the repository's database setup instructions.
3. Run `npm install` in this directory.
4. Run `npm run dev` and open `http://127.0.0.1:5173`.

The Vite server binds to loopback. The backend is local-only until authentication and per-user authorization are implemented. The API defaults to `http://127.0.0.1:8000`; copy `.env.example` to `.env.local` only if you need to set `VITE_API_BASE_URL` explicitly. Point it only at the local FastAPI address.

## Available Scripts

- `npm run dev`: Launch the local development server.
- `npm run build`: Compile production bundle.
- `npm run preview`: Preview production build locally.
- `npm test`: Run central API client contract and error-handling tests.
