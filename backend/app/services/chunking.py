"""Token-aware chunking for indexing pipelines."""
import logging
import re
import uuid
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

TOKEN_RE = re.compile(r"\S+")

DEFAULT_CHUNK_TOKENS = 300
DEFAULT_OVERLAP_TOKENS = 50


class TokenChunker:
    """Split text into overlapping token windows.

    Each chunk carries a stable ``chunk_id`` so re-indexing the same document
    produces the same identifiers, which keeps vector collections stable.
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_TOKENS,
        chunk_overlap: int = DEFAULT_OVERLAP_TOKENS,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be >= 0 and smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @staticmethod
    def count_tokens(text: str) -> int:
        """Count whitespace-delimited tokens."""
        return len(TOKEN_RE.findall(text or ""))

    def split(self, text: str) -> List[str]:
        """Return the raw token windows of ``text``."""
        tokens = TOKEN_RE.findall(text or "")
        if not tokens:
            return []

        step = self.chunk_size - self.chunk_overlap
        windows: List[str] = []
        for start in range(0, len(tokens), step):
            window = tokens[start : start + self.chunk_size]
            if not window:
                break
            windows.append(" ".join(window))
            if start + self.chunk_size >= len(tokens):
                break
        return windows

    def chunk(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        prefix: str = "chunk",
    ) -> List[Dict[str, Any]]:
        """Chunk ``text`` and attach metadata, ids and positions."""
        windows = self.split(text)
        if not windows:
            return []

        base_metadata = dict(metadata or {})
        document_id = base_metadata.get("doc_id") or base_metadata.get("document_id")
        chunks: List[Dict[str, Any]] = []
        cursor = 0

        for index, window in enumerate(windows):
            start_char = text.find(window, cursor) if text else 0
            if start_char < 0:
                start_char = cursor
            end_char = start_char + len(window)
            cursor = end_char

            chunk_id = self._chunk_id(document_id, index)
            chunk_metadata = {
                **base_metadata,
                "chunk_index": index,
                "start_char": start_char,
                "end_char": end_char,
            }
            if document_id is not None:
                chunk_metadata.setdefault("doc_id", str(document_id))

            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "id": chunk_id,
                    "content": window,
                    "metadata": chunk_metadata,
                    "token_count": self.count_tokens(window),
                    "chunk_index": index,
                    "start_char": start_char,
                    "end_char": end_char,
                }
            )

        logger.debug("Produced %d chunks from %d tokens", len(chunks), self.count_tokens(text))
        return chunks

    @staticmethod
    def _chunk_id(document_id: Any, index: int) -> str:
        if document_id is None:
            return f"chunk_{uuid.uuid4().hex}"
        return f"{document_id}:{index}"

    def chunk_many(
        self,
        texts: Iterable[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Chunk several documents in one call."""
        collected: List[Dict[str, Any]] = []
        for position, text in enumerate(texts):
            metadata = metadatas[position] if metadatas and position < len(metadatas) else None
            collected.extend(self.chunk(text, metadata))
        return collected


token_chunker = TokenChunker()