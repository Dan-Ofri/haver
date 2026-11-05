# 1. Domain plugins on a domain-agnostic core

Date: 2026-11-05. Status: accepted.

## Context
The product starts with training and sleep and must grow to nutrition, stress, calendar and more
without rewrites.

## Decision
A core package (`haver.core`) owns the agent loop, tool registry, retrieval, memory, safety and
evaluation. Each domain is a plugin package (`haver.plugins.<name>`) that contributes its tools,
tables, knowledge documents, red-flag rules and eval questions through one interface.
The core never imports a plugin; a test enforces it.

## Consequences
Adding a domain should touch only that domain's folder. We will measure this when nutrition and
stress are added. The plugin interface must stay small, or every plugin pays for its complexity.
