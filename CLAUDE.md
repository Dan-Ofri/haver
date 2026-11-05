# Guide for AI coding agents

Read `docs/SPEC.md` and `docs/adr/` before changing behaviour. The spec is the source of truth.

## Rules

- `haver.core` never imports from `haver.plugins`. A domain plugs into the core, not the reverse.
- Every behaviour change comes with a test. Agent behaviour is tested with a fake LLM, never with a
  real provider in CI.
- Validate every tool input and every model output with Pydantic before using it.
- Numbers shown to the user are computed in code, never by the model.
- Never commit secrets or personal data. Only synthetic demo data lives in the repository.
- Keep it simple. Add a dependency or an abstraction only when a current need requires it.

## Commands

- Backend: `cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy src tests && uv run pytest`
- Frontend: `cd frontend && npm run lint && npm run typecheck && npm test && npm run build`
- Full stack: `docker compose up --build`, then http://localhost:8080

## Workflow

Branch from `develop`, open a pull request to `develop`, conventional commit messages. See
`CONTRIBUTING.md`.
