# Contributing

## Branches

- `main` is always stable and deployable. It changes only through a pull request from `develop`.
- `develop` is the integration branch.
- Work happens on short-lived branches from `develop`: `feat/...`, `fix/...`, `chore/...`, `docs/...`.

## Pull requests

1. Small and focused, linked to the spec item it serves.
2. CI must be green: lint, format, type checks, tests, builds and secret scanning.
3. Every pull request gets an independent review from a reviewer with no prior context (a fresh
   AI reviewer agent), and the findings are fixed or answered before human review.
4. The owner reviews and merges.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `chore:`,
`test:`, `refactor:`, `ci:`.

## Decisions

Any choice that is costly to reverse gets a short ADR in `docs/adr`.
