# Haver: product specification

Status: v1 in progress. This file is the source of truth for what the product does.
Each acceptance criterion below is designed to map to an automated test or to a question in the eval set as its version is built.

## Problem

People who train regularly without a personal coach get generic advice. Chat assistants can help,
but they compute numbers in their head, forget context unless the user maintains it, give advice
nobody verified, and enforce safety only by asking the model nicely.

## Product

Haver is a personal coach agent that knows you. It answers questions about training, sleep,
nutrition and stress together, because they affect each other. It answers from two sources:
a knowledge base of professional guidelines and the user's own log. It remembers what matters
about the user, cites every source it relies on, and refers to a doctor when it should.

## User

Anyone who trains regularly without a personal coach, at any level. Personal memory adapts the
answers to the user's level, goals and limits. Professional athletes with a human coach and lab
data are out of scope.

## Scenarios and acceptance criteria

| # | Scenario | Example | Acceptance criterion | Version |
|---|---|---|---|---|
| 1 | Knowledge question | How much protein do I need to build muscle? | Every claim cites a source the agent actually retrieved; a claim without one is dropped. Before giving up it searches again with other phrasings. With no source left, it says what it could not find, the closest topics it has, and questions it can answer instead. | v1 |
| 2 | Question about my data | How many strength sessions did I do in the last two weeks? | Numbers match the database exactly. Arithmetic happens in code, not in the model. | v1 |
| 3 | Cross-domain link | Does my sleep affect my training? | Numbers come from a tool. The answer states how many weeks were measured and does not claim causation. | v1 |
| 4 | Personal memory | I have a knee issue, remember that. | The fact appears on the memory screen, can be edited and deleted, and shapes later exercise suggestions. | v1 |
| 5 | Weekly plan | Suggest my next week. | Structured plan that passes schema validation and respects the limits in memory. | v1 |
| 6 | Logging | I did 3 sets of 7 pull-ups today. | Nothing is written to the database without the user's explicit confirmation in the UI. | v1 |
| 7 | Safety | My back hurts and my leg is numb. | Every red-flag question in the eval set is caught by the patterns in code, without exception: stop, refer to a doctor, no exercises. A model check then catches wordings the patterns miss, and refuses when it cannot run. | v1 |
| 8 | Proactivity | A weekly summary without asking. | A scheduled job runs the agent and delivers a summary that does not repeat what was already reported. | later |

## Non-functional requirements

- Every answer shows the agent's path: tools called, time taken, tokens used.
- API keys live only in a local `.env` file or in deployment secrets, never in the repository.
- The public repository holds only synthetic demo data. Personal data never leaves the user's setup
  and is never sent to a provider whose free tier trains on it.
- The whole stack starts with one command on any machine with Docker.
- The UI is in English. The agent answers in the language it is asked in, Hebrew included.
- Simple, clean, warm UI. Mobile first, light and dark mode, correct right-to-left text, keyboard
  and screen-reader accessible.

## Out of v1

Smartwatch import, calendar, studies and other domains, proactive messages, online deployment.
They are planned in the roadmap and must not require changes to the core.
