"""Embedding service with a deterministic offline fallback.

When an OpenAI API key is configured the service delegates to the embeddings API.
Otherwise it falls back to a hashed bag-of-words projection so that indexing,
search and the whole pipeline stay functional in development and CI.
"""
import hashlib
import logging
import math
import re
from collections import OrderedDict
from typing import Any, Dict, Iterable, List, Sequence

from backend.config import LLM_EMBEDDING_MODEL, OPENAI_API_KEY

logger = logging.getLogger(__name__)

HASHED_VECTOR_SIZE = 384
TOKEN_RE = re.compile(r"[\w']+", re.UNICODE)

_OPENAI_VECTOR_SIZES = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


def _tokenize(text: str) -> List[str]:
    return [token.lower() for token in TOKEN_RE.findall(text or "")]


class EmbeddingService:
    """Produce L2-normalised vectors for text and batches of text."""

    def __init__(self, model: str | None = None, cache_size: int = 2048):
        self.model = model or LLM_EMBEDDING_MODEL
        self._client: Any | None = None
        self._vector_size = _OPENAI_VECTOR_SIZES.get(self.model, HASHED_VECTOR_SIZE)
        self._cache: OrderedDict[str, List[float]] = OrderedDict()
        self._cache_size = cache_size

    @property
    def vector_size(self) -> int:
        """Dimensionality of the vectors this service returns."""
        return self._vector_size

    @property
    def provider(self) -> str:
        return "openai" if self._client is not None else "hashed"

    def _openai_client(self) -> Any | None:
        if self._client is not None:
            return self._client
        if not OPENAI_API_KEY:
            return None
        try:
            from openai import OpenAI

            self._client = OpenAI(api_key=OPENAI_API_KEY)
        except Exception:
            logger.exception("Falling back to hashed embeddings: OpenAI client unavailable")
            self._client = None
        return self._client

    def _embed_openai(self, texts: Sequence[str]) -> List[List[float]]:
        client = self._openai_client()
        response = client.embeddings.create(model=self.model, input=list(texts))
        vectors = [item.embedding for item in response.data]
        if vectors:
            self._vector_size = len(vectors[0])
        return [self._normalize(vector) for vector in vectors]

    @staticmethod
    def _normalize(vector: Sequence[float]) -> List[float]:
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return list(vector)
        return [value / norm for value in vector]

    def _embed_hashed(self, text: str) -> List[float]:
        vector = [0.0] * self._vector_size
        tokens = _tokenize(text)
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode()).digest()
            bucket = int.from_bytes(digest[:4], "big") % self._vector_size
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        return self._normalize(vector)

    def _cache_get(self, key: str) -> List[float] | None:
        cached = self._cache.get(key)
        if cached is not None:
            self._cache.move_to_end(key)
        return cached

    def _cache_put(self, key: str, vector: List[float]) -> None:
        self._cache[key] = vector
        self._cache.move_to_end(key)
        while len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

    def embed_query(self, text: str) -> List[float]:
        """Embed a single string."""
        vectors = self.embed([text])
        return vectors[0]

    def embed(self, texts: Iterable[str] | str) -> List[List[float]]:
        """Embed one or many strings, using the cache where possible."""
        if isinstance(texts, str):
            texts = [texts]
        batch = list(texts)
        if not batch:
            return []

        pending: List[int] = []
        vectors: List[List[float] | None] = [None] * len(batch)
        for position, text in enumerate(batch):
            key = f"{self.model}:{text}"
            cached = self._cache_get(key)
            if cached is None:
                pending.append(position)
            else:
                vectors[position] = cached

        if pending:
            subset = [batch[position] for position in pending]
            if self._openai_client() is not None:
                try:
                    produced = self._embed_openai(subset)
                except Exception:
                    logger.exception("OpenAI embedding call failed; using hashed embeddings")
                    produced = [self._embed_hashed(text) for text in subset]
            else:
                produced = [self._embed_hashed(text) for text in subset]

            for position, text, vector in zip(pending, subset, produced):
                vectors[position] = vector
                self._cache_put(f"{self.model}:{text}", vector)

        return [vector if vector is not None else self._embed_hashed("") for vector in vectors]

    def embed_documents(self, documents: Sequence[Dict[str, Any]], text_key: str = "content") -> List[List[float]]:
        """Embed the text field of a list of documents."""
        return self.embed([str(document.get(text_key, "")) for document in documents])


embedding_service = EmbeddingService()