# Steadwork Tech Job Board

Standalone React/Vite frontend with an included mock service. API mode is the default for normal development; use `VITE_DATA_MODE=mock` for isolated frontend work. This folder uses npm and does not depend on the root Replit pnpm workspace.

## Copy into your project

After exporting the repository, copy the contents of `artifacts/tech-job-board` into your project's `frontend/` folder. Open a terminal in `frontend/` and run:

```sh
npm ci
npm run dev
```

Open `http://localhost:5173`.

## Checks

```sh
npm test
npm run typecheck
npm run build
```

## Service layer

- `src/services/job-board-service.ts` defines the interface used by the UI.
- `src/services/mock-job-board-service.ts` is the opt-in mock implementation and persists demo data in browser storage.
- `src/services/http-job-board-service.ts` is the default typed HTTP adapter.
- `src/services/index.ts` selects the implementation.
- `backend-plan.md` records the proposed API contract and the backend-stack choice to resolve.

The mock does not store passwords, send verification or reset emails, or upload CV contents. Vite proxies `/api` to `http://localhost:8000` by default (override with `API_PROXY_TARGET`). Set `VITE_DATA_MODE=mock` to use mock data; API failures never fall back to mock data.
