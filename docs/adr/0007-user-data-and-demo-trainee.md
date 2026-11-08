# 7. User data tables per plugin, and a made-up demo trainee

Date: 2026-11-08. Status: accepted.

## Context
Scenarios 2 and 3 need the user's own logs: what they did, how they slept, and how the two relate.
The core must stay domain-agnostic, and the public repository may hold only synthetic data.

## Decision
A plugin declares its tables as `Plugin.schema`; the app runs every schema at first use. Training
owns `workouts`, sleep owns `sleep_logs`, each with one read-only tool whose numbers come from SQL.
A third plugin, `insights`, is the only place that reads two domains' tables: it compares weekly
average sleep with weekly strength minutes, in code, over weeks with at least 5 logged nights and
one logged workout (so a gap in either log is not read as short sleep or skipped training), needs
at least 6 such weeks, adds a small-sample caveat under 10, and always says it is an association, not causation.
`SEED_DEMO_DATA` fills empty logs with 12 weeks of a made-up trainee, with a short-sleep/skipped-
strength link built in. It is off by default, takes an advisory lock so concurrent starts seed once, and does nothing
while either log has rows. If the flag stays on and a user deletes every row, the next start
seeds the demo again.

## Consequences
Domains stay unaware of each other; cross-domain questions live in `insights`. Writing to the logs
(scenario 6, with confirmation) and importing real data are later work. Source links for log
answers point to `#your-log`, as there is no page behind them yet.
