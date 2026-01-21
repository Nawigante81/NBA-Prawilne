# Repository Guidelines

## Project Structure & Module Organization
- Frontend app lives in `src/` with React + Vite entry points like `src/main.tsx` and `src/App.tsx`.
- Backend API and data tooling are in `backend/` (FastAPI app in `backend/main.py`, utilities like `analytics.py`, SQL in `backend/*.sql`).
- Supabase SQL assets are in `supabase/`, deployment configs in `deploy/`, and helper scripts in `scripts/`.
- Built frontend output is `dist/` (generated), and docs are centralized in `docs/`.
- Frontend tests are in `src/tests/`; backend tests follow `backend/test_*.py`.

## Build, Test, and Development Commands
- `npm run dev`: start the Vite frontend locally.
- `npm run build`: produce production frontend assets in `dist/`.
- `npm run preview`: serve the built frontend for verification.
- `npm run lint`: run ESLint on TypeScript/React files.
- `npm run typecheck`: run TypeScript type checks.
- `npm run test` / `npm run test:run` / `npm run test:coverage`: run Vitest in watch, CI, or coverage mode.
- `./setup.sh`: one-time setup for deps and environment (Linux/Mac).
- `./start.sh`: run frontend + backend together (uses `.env`).
- Backend dev: `cd backend && source venv/bin/activate && python -m uvicorn main:app --reload`.

## Coding Style & Naming Conventions
- Frontend uses TypeScript + React; keep 2-space indentation and prefer functional components.
- ESLint is configured in `eslint.config.js`; fix lint before PRs.
- Tailwind CSS is used; keep utility classes grouped logically.
- Python follows standard 4-space indentation and `snake_case` for functions/files.

## Testing Guidelines
- Frontend uses Vitest (`src/tests/*.test.tsx`). Prefer `*.test.tsx` naming.
- Backend uses Pytest (`backend/test_*.py`). Run from `backend/` with `pytest`.
- Add tests for new features or bug fixes, especially around analytics and data transforms.

## Commit & Pull Request Guidelines
- Git history does not show a strict convention; keep commit messages concise and descriptive (avoid single-letter messages).
- PRs should include a brief summary, how to test, and link any relevant issues.
- Include screenshots or GIFs for UI changes, plus notes on data sources affected.

## Configuration & Data Notes
- Environment config lives in `.env` / `.env.production`. Keep secrets out of git.
- Large datasets belong in local `data/` (gitignored) rather than the repo.
- Supabase setup scripts live in `supabase/`; update docs if schemas change.
