# 3. One PostgreSQL database with pgvector, hybrid retrieval

Date: 2026-11-05. Status: accepted.

## Context
The agent needs relational data (the user's log, memory) and semantic search over knowledge
documents.

## Decision
PostgreSQL with the pgvector extension stores both. Retrieval combines vector similarity with
full-text keyword search and merges the rankings (reciprocal rank fusion).

## Consequences
One service to run and back up. Exact terms such as exercise names are still found when vector
search misses them.

## Implementation (phase 3b)
- Embeddings are 768 dimensions (Gemini `gemini-embedding-2` with `output_dimensionality`), stored in
  a `vector(768)` column with the model name and a content hash. A document is embedded again only
  when its text or the model changed.
- Without an API key, a hashed bag-of-words embedder is used. It matches shared words only, so
  the eval case that needs meaning-based search is skipped for it.
- Each ranking contributes its top 10 and the fusion constant is 60. Vector results below a
  per-embedder minimum cosine similarity are dropped, so an unrelated question finds nothing.
- The Gemini minimum (0.5) is a first guess and is not yet calibrated with real data.
- No vector index yet: with a handful of documents an exact scan is faster and exact.
