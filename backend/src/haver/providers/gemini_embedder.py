"""Gemini embeddings through the google-genai SDK."""

import math

from google import genai
from google.genai import types

from haver.core.embedding import DIMENSIONS


class GeminiEmbedder:
    # Not calibrated against real data yet: tune with the eval set (see ADR 0003).
    min_similarity = 0.5

    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self.name = f"{model}-{DIMENSIONS}"

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.models.embed_content(
            model=self._model,
            contents=texts,
            config=types.EmbedContentConfig(output_dimensionality=DIMENSIONS),
        )
        vectors = [list(e.values or []) for e in response.embeddings or []]
        if len(vectors) != len(texts) or any(len(v) != DIMENSIONS for v in vectors):
            raise ValueError("unexpected embedding response shape")
        # Shortened vectors are not unit length, so normalise them.
        return [[x / (math.sqrt(sum(y * y for y in v)) or 1.0) for x in v] for v in vectors]
