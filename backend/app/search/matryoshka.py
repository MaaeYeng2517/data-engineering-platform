import numpy as np


def matryoshka_embedding(embedding: np.ndarray, prefix_dims: int) -> np.ndarray:
    if embedding.ndim != 1:
        raise ValueError("embedding must be 1D")
    prefix_dims = max(1, min(prefix_dims, embedding.shape[0]))
    prefix = embedding[:prefix_dims]
    norm = np.linalg.norm(prefix)
    if norm == 0:
        return prefix
    return prefix / norm


def mrl_train_embeddings(
    embeddings: np.ndarray, prefix_list: list[int]
) -> dict[int, np.ndarray]:
    if embeddings.ndim != 2:
        raise ValueError("embeddings must be 2D (n, d)")
    results = {}
    for d in prefix_list:
        if d < 1:
            continue
        d = min(d, embeddings.shape[1])
        pref = embeddings[:, :d]
        norms = np.linalg.norm(pref, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        results[d] = (pref / norms).astype(float)
    return results
