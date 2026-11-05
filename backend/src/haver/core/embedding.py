"""Provider-neutral interface for turning text into vectors."""

from typing import Protocol

DIMENSIONS = 768


class Embedder(Protocol):
    # Stored with every vector: vectors from different models are never compared.
    name: str
    # Cosine similarity below this is treated as unrelated. The scale differs per model.
    min_similarity: float

    def embed(self, texts: list[str]) -> list[list[float]]:
        """One unit-length vector of DIMENSIONS floats per text."""
        ...
