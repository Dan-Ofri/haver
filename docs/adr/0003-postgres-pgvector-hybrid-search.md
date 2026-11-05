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
