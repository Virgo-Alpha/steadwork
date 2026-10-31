# Steadwork Tech Job Board

Responsive job-board frontend with a mock service layer. The mock is the default, so candidate, guest, and employer flows run without a backend.

## Run locally

Export or clone the **whole repository**. This app is a pnpm workspace package and uses shared workspace dependencies, so downloading only this folder is not sufficient.

From the repository root:

```sh
pnpm install --frozen-lockfile
PORT=5173 BASE_PATH=/ pnpm --filter @workspace/tech-job-board run dev
```

Open `http://localhost:5173`.

On Windows PowerShell:

```powershell
pnpm install --frozen-lockfile
$env:PORT="5173"
$env:BASE_PATH="/"
pnpm --filter @workspace/tech-job-board run dev
```

## Checks

```sh
pnpm --filter @workspace/tech-job-board run test
pnpm --filter @workspace/tech-job-board run typecheck
PORT=5173 BASE_PATH=/ pnpm --filter @workspace/tech-job-board run build
```

## Service layer

- `src/services/job-board-service.ts` defines the interface used by the UI.
- `src/services/mock-job-board-service.ts` is the default implementation and persists demo data in browser storage.
- `src/services/http-job-board-service.ts` is the typed HTTP adapter for a future API.
- `src/services/index.ts` selects the implementation.
- `backend-plan.md` records the proposed API contract and the unresolved backend-stack choice.

The mock does not store passwords, send verification or reset emails, or upload CV contents. The HTTP adapter is not connected to a running backend. Set `VITE_DATA_MODE=api` only when the matching API endpoints are available.
