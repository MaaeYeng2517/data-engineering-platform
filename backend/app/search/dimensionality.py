import numpy as np
from sklearn.decomposition import PCA
from typing import List, Union


def reduce_embeddings_pca(
    embeddings: Union[np.ndarray, List[List[float]]],
    n_components: int = 3,
) -> np.ndarray:
    if isinstance(embeddings, list):
        embeddings = np.array(embeddings, dtype=float)
    if embeddings.ndim != 2:
        raise ValueError("embeddings must be 2D array of shape (n_samples, n_features)")
    n_samples, n_features = embeddings.shape
    if n_components > n_features:
        n_components = n_features
    pca = PCA(n_components=n_components)
    reduced = pca.fit_transform(embeddings)
    return reduced.astype(float)
