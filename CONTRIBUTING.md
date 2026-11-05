# Contributing

## Branches

- `main` is always stable and deployable. It changes only through a pull request from `develop`.
- `develop` is the integration branch.
- Work happens on short-lived branches from `develop`: `feat/...`, `fix/...`, `chore/...`, `docs/...`.

## Pull requests

1. Small and focused, linked to the spec item it serves.
2. CI must be green: lint, backend format check, type checks, tests, builds and secret scanning.
3. Every pull request gets an independent review from a reviewer with no prior context (a fresh
   AI reviewer agent). After blocking findings are fixed, a new fresh reviewer checks again, until
   one approves. Non-blocking suggestions do not start another round. After three rounds without
   approval, the owner decides.
4. The owner reads a short summary of the pull request (what changed, decisions and why, how it
   was checked, open questions) and approves it before it is merged.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `chore:`,
`test:`, `refactor:`, `ci:`.

## Decisions

Any choice that is costly to reverse gets a short ADR in `docs/adr`.
