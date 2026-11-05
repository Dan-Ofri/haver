"""A keyless embedder for local runs and CI: hashed bag of words.

It matches shared words only. It proves the wiring, not semantic search.
"""

import hashlib
import math
import re

from haver.core.embedding import DIMENSIONS

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "can",
        "do",
        "does",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "it",
        "me",
        "my",
        "need",
        "of",
        "on",
        "or",
        "should",
        "the",
        "to",
        "what",
        "with",
        "you",
    }
)


class HashingEmbedder:
    name = "offline-hash-v1"
    min_similarity = 0.1

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * DIMENSIONS
        for word in re.findall(r"\w+", text.lower()):
            if word in STOPWORDS:
                continue
            digest = hashlib.blake2b(word.encode(), digest_size=4).digest()
            vector[int.from_bytes(digest, "big") % DIMENSIONS] += 1.0
        norm = math.sqrt(sum(x * x for x in vector))
        return [x / norm for x in vector] if norm else vector
