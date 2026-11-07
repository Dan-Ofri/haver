# 6. Two safety layers: patterns, then a model check

Date: 2026-11-08. Status: accepted.

## Context
Red-flag patterns in code are free, instant and cannot be argued with, but no list of patterns
covers every way a person can describe a warning sign. Each review of the patterns found new
wordings they missed.

## Decision
Patterns run first. If none matches, one short call asks the model only to name the red flag the
question describes, or "none". It gets no tools and no memory. A flag gets its fixed message and
the agent is not called. A failed call or an answer out of format refuses the question, with a
message that still points to emergency help.

## Consequences
Every question that passes the patterns costs one extra model call, a few hundred tokens and
some latency. "The model is not called" now holds only for pattern hits. A crafted message can
still talk the model into "none", so the model check adds coverage on top of the patterns and
never replaces them. Without a real model (offline, CI) the check answers "none", so its quality
is measured with `python -m haver.evals --safety` against a real provider.
