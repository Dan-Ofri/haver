# Build state

How the build stands and how the work is run. Written on 2026-11-08 so that a new working
session can start from the repository alone. The spec (`docs/SPEC.md`) is the source of truth for
behaviour, `docs/adr/` for decisions. This file is the only place for status and working rules,
and is updated in the same PR as the work it describes.

## What Haver is

A personal coach agent that knows you: training, sleep, nutrition and stress together. It answers
from a knowledge base of guidelines and from the user's own logs, remembers what matters about
the user, cites every source, and refers to a doctor when it should. It is a portfolio project
for a junior full-stack AI role (Moveo Group), so the build is deliberately professional:
spec-driven, reviewed, tested and measured. The owner is Dan (GitHub `Dan-Ofri`).

Stack: React + TypeScript + Vite, FastAPI, hand-written agent loop (ADR 4), PostgreSQL +
pgvector with hybrid search (ADR 3), Gemini free tier behind a provider layer (ADR 2), Docker
Compose, GitHub Actions. Domains are plugins on a domain-agnostic core (ADR 1). The repository is
public and holds only synthetic data.

## Where we are

`main` is still the initial commit. All work is on `develop`; a release PR `develop` to `main`
comes later.

| PR | What | Status |
|---|---|---|
| 1 | Foundations: repo, CI, spec, folders, containers | merged |
| 2 | Walking skeleton: chat to server to agent loop to answer | merged |
| 3 | Grounded answers (claims need retrieved sources), helpful "not found", plugin interface | merged |
| 4 | Hybrid search: full-text + embeddings, rank fusion | merged |
| 5 | Personal memory API and `remember` tool | merged |
| 6 | Red-flag safety by patterns in code, English and Hebrew | merged |
| 7 | Memory screen in the UI | merged |
| 8 | Second safety layer: a model classifies what the patterns miss, fails closed (ADR 6) | merged |
| 9 | Phase 4: `workouts` and `sleep_logs`, summary tools, `insights` plugin with the sleep and training link, demo trainee (ADR 7) | merged |

## Open items

1. **Gemini calibration is unrun.** Against a real Gemini key, nothing has been measured yet:
   whether `gemini-embedding-2` is the right model name, whether the minimum similarity of 0.5 is
   right, and how good the model safety layer is. Run `uv run python -m haver.evals` and
   `uv run python -m haver.evals --safety` from `backend/` on Dan's machine, where the key lives
   in an untracked `.env`. A Remote Control card for this was posted and has not been answered.
   Never read or print the key.
2. **Scenarios still to build** (see the table in `docs/SPEC.md`): 5 weekly plan with schema
   validation, 6 logging with explicit confirmation in the UI, and eval cases for the log tools.
   Then the design phase (mock-ups Dan approves before the full UI), polish and the application.
3. **Red-flag patterns** should be reviewed by Dan's sister, who is a physiotherapist.
4. **Release PR** `develop` to `main` when a phase is complete.
5. **Later**: nutrition and stress as plugins (the test of the plugin design: a new domain
   touches only its own folder), real data import, proactive weekly summary, deployment
   (frontend on Cloudflare, backend host to be chosen, see ADR 5).

## How the work is run (Dan's rules)

- Branch from `develop`, one focused PR to `develop`, conventional commits.
- Every behaviour change ships with its own test. Agent behaviour is tested with a fake LLM,
  never a real provider in CI.
- **Review loop.** A fresh-context reviewer reads each PR against the spec. When it finds
  blocking problems and they are fixed, a new reviewer runs, until one approves. More than three
  rounds: tell Dan. Every fix needs its own test, or the next reviewer blocks on it. In practice
  each PR needs two or three rounds and every round has found real issues.
- **Token use.** The first full review runs on the main model. Later rounds are narrow (only the
  fix diff) and can run on a smaller model. Start a fresh session when the context gets long.
- **Approval.** After review, send Dan a short Hebrew summary: what changed, the decisions and why,
  how it was checked, what needs him. Merge only after he says approved ("מאושר", "מאשר" or
  "אפשר להמשיך"). Required check on `main`: CI Gatekeeper.
- Dan has given standing approval to run commands on his own machine (through Remote Control);
  ask only for something sensitive. Do not ask him to run terminal commands himself.
- Dan prefers verified claims, short direct communication, and a recommendation instead of a list
  of options.

## Design decisions to keep

- Helpful "not found": no claim without a retrieved source; the agent retries with other wordings,
  then says what it could not find, what is close, and what it can answer instead.
- Safety is enforced in code: patterns first, then a model check; if the check cannot run, the
  question is refused with a message that still points to emergency help. A crafted message can
  still fool the model check, so it adds coverage and never replaces the patterns.
- Numbers shown to the user are computed in SQL or code, never by the model. A correlation always
  states how many weeks it used and that it is an association, not causation.
- Free-tier Gemini may train on what it receives: demo data only, never Dan's real data. Real
  personal data needs a provider and plan that do not train on it.
- Plugins declare their tables with `Plugin.schema`. Only the `insights` plugin reads more than
  one domain's tables.
- `SEED_DEMO_DATA` fills empty logs with a made-up trainee. Off by default, on in
  `docker-compose.yml`.

## Working in the cloud container

Start `dockerd` by hand, then run the test database:

```bash
docker run -d --rm --name haver-test-db -p 127.0.0.1:5432:5432 \
  -e POSTGRES_USER=haver -e POSTGRES_PASSWORD=haver -e POSTGRES_DB=haver pgvector/pgvector:pg17
```

Tests use the database `haver_test`. Backend checks:
`cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy src tests && uv run pytest`.
Docker Hub can rate-limit base images; the CI docker job is the source of truth. The container
cannot always reach GitHub with git; PRs go through the GitHub tools.
