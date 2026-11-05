# Haver

**A personal coach that knows you.** Haver answers questions about your training, sleep,
nutrition and stress together, from professional guidelines and from your own log. It remembers
what matters about you, cites every source, and knows when to send you to a doctor.

> Status: early development. See the [roadmap](#roadmap).

## Why not just a chat assistant?

A chat assistant works for a power user who manages it. Haver is designed to do in code what a
chat leaves to the user (planned for v1, see the [roadmap](#roadmap)):

- **Numbers come from your data**, computed by tools, not estimated by the model.
- **Safety is enforced in code**, not requested in a prompt.
- **Memory you can see and edit**, instead of context you have to maintain.
- **Every answer is grounded**: citations are checked against what the agent actually retrieved.
- **Quality is measured** by an eval set, not judged by feel.

## Architecture

```
React + TypeScript UI  ->  FastAPI server  ->  agent loop  <->  LLM provider (Gemini / Groq)
                                                   |
                         tools from the core and from each domain plugin
                                                   |
                              PostgreSQL + pgvector (knowledge, memory, log)
```

Domains are plugins on a domain-agnostic core: adding one should touch only its own folder.
Decisions and their reasons are recorded in [docs/adr](docs/adr). The product spec, with an
acceptance criterion for every scenario, is in [docs/SPEC.md](docs/SPEC.md).

## Run it

Requirements: Docker.

```bash
cp .env.example .env      # then add your keys
docker compose up --build
```

Open http://localhost:8080.

## Develop

Backend (Python 3.13, [uv](https://docs.astral.sh/uv/)):

```bash
docker compose up -d db   # the database, from the repository root
cd backend
uv sync
uv run ruff check . && uv run ruff format --check . && uv run mypy src tests && uv run pytest
uv run uvicorn haver.main:app --reload
```

Frontend (Node 22):

```bash
cd frontend
npm ci
npm run lint && npm run typecheck && npm test && npm run build
npm run dev
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the branch and review workflow.

## Roadmap

1. Foundations: repository, spec, CI, containers
2. End-to-end skeleton: one question through every layer
3. Core: plugin interface, hybrid search, memory, validation, safety
4. Training and sleep plugins, synthetic athlete, eval set
5. Design and user experience
6. Polish and demo
7. Nutrition and stress plugins, as proof of the plugin design
8. Live deployment
9. Later: proactivity, smartwatch import, more domains

## License

Code: MIT. Knowledge-base documents keep the license of their source.
