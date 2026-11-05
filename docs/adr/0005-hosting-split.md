# 5. Frontend on Cloudflare, backend on a container host

Date: 2026-11-05. Status: proposed, to confirm in phase 8.

## Context
The plan was to host everything on Cloudflare. Python Workers are generally available since
September 2026 and run FastAPI, with Postgres through Hyperdrive. This was checked against the
documentation, not yet deployed:

- The free plan allows 10 ms of CPU time per request. Waiting on the network does not count, but
  the Python runtime, FastAPI routing and Pydantic validation all run on CPU, and the agent loop
  parses several model responses per question.
- Only pure-Python packages and packages built for WebAssembly load. The google-genai SDK is not
  on the list of packages reported to work.
- The free plan allows 50 subrequests per request. Each agent step is at least one.

Sources: [Workers limits](https://developers.cloudflare.com/workers/platform/limits/),
[Python Workers package constraints](https://www.issoh.co.jp/tech/details/18259/).

## Decision
The frontend is a static build and goes on Cloudflare. The backend stays a standard container, so
it can run on any free container host. The host is chosen in phase 8.

## Consequences
The backend keeps its normal Python dependencies. A hands-on test on Python Workers is still worth
one hour in phase 8: if a request fits in 10 ms of CPU, the whole product can live on Cloudflare.
