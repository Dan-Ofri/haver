# 4. A hand-written agent loop instead of a framework

Date: 2026-11-05. Status: accepted.

## Context
Frameworks such as LangChain or LangGraph hide the loop, the validation and the stopping rules.

## Decision
The loop is our own code: call the model, validate every tool input, run the tool, validate the
final answer and its citations, stop at a step limit.

## Consequences
Full control and easy to explain. We own retries, limits and tracing, so they need tests.
