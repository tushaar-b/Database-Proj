# IntelliVest investor workspace (React + Vite)

Responsive local dashboard for cash flow, affordable recommendations, portfolios, PostgreSQL risk metrics, and alerts. Financial results are read from FastAPI; the frontend does not connect directly to PostgreSQL.

## Local setup

1. Start the FastAPI backend and both PostgreSQL databases using the repository instructions.
2. Configure the local database URLs and password in the backend environment using the repository's database setup instructions.
3. Run `npm install` in this directory.
4. Run `npm run dev` and open `http://127.0.0.1:5173`.

The Vite server binds to `127.0.0.1:5173` with `strictPort`, so it will not silently switch to a port missing from the backend origin allowlist. Use that URL consistently. Both development and preview proxy `/api` to the backend using `APP_HOST` and `APP_PORT` from the root `.env` (defaults: `127.0.0.1:8000`). Session cookies remain host-only, HttpOnly and SameSite=Lax; the proxy preserves the browser Origin for backend CSRF validation.

`VITE_API_BASE_URL` defaults to `/api`. Remove an old `frontend/.env.local` override or set `VITE_API_BASE_URL=/api`. For a direct local API override, the client aligns loopback hostnames with the page hostname while retaining the configured API port. Do not mix browser tabs at `localhost` and `127.0.0.1`: those are separate cookie hosts. If you change the frontend origin, also update root `ALLOWED_ORIGINS`. Restart Vite after changing environment settings.

Start the backend from the project root with `.venv/bin/python -m backend`; this uses the same root `APP_HOST`/`APP_PORT` settings as the proxy. Production static hosting must reverse-proxy `/api` to FastAPI, or build with an explicit API URL and corresponding allowed origin. The gateway remains restricted to local clients.

Authentication has one shared session controller. Strict Mode initialization shares a single `/auth/me` request. Only a 401 belonging to the currently authenticated session expires it; an initial unauthenticated check or incorrect password does not. Responses from an older session cannot replace a newer identity or CSRF token. Only one login form renders. A failed logout retains the current session and reports the error.

CSRF proofs are stable within each opaque session, including concurrent `/auth/me` calls and separate tabs using the same session. Existing sessions upgrade their stored proof on their first `/auth/me` call; no schema migration or data reset is required. A browser page still running the old bundle should be reloaded after this backend change.

## Available Scripts

- `npm run dev`: Launch the local development server.
- `npm run build`: Compile production bundle.
- `npm run preview`: Preview production build locally.
- `npm test`: Run central API client contract and error-handling tests.
