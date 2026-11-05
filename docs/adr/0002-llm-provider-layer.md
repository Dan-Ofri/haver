# 2. Provider-neutral LLM layer, Gemini and Groq first

Date: 2026-11-05. Status: accepted.

## Context
The project runs on free tiers. Gemini's free tier is the strongest free model with tool calling
and Hebrew, but Google's terms allow free-tier content to be used for product improvement and read
by human reviewers. Groq's free tier serves open models and its policy says it does not train on
API data.

## Decision
The agent talks to a small internal interface, not to a vendor SDK. Gemini is the default for the
public demo with synthetic data. Groq is the option for personal data. The choice between them is
made by running the eval set on both.

## Consequences
Switching provider is a configuration change. Provider-specific features are used only behind the
interface.
