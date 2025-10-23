"""Embedding generation using sentence-transformers

PERFORMANCE: Includes caching to avoid regenerating embeddings for identical texts.
This reduces memory spikes and computation time in the clustering pipeline.
"""

from typing import List

import numpy as np
from app.services.service_registry import get_embedding_model
from app.services.embedding_cache import (
    get_cached_embeddings,
    cache_embeddings,
    get_cache_stats,
)


def get_model():
    """Get the singleton embedding model instance"""
    return get_embedding_model()


def generate_embeddings(texts: List[str]) -> np.ndarray:
    """
    Generate embeddings for a list of texts with caching.

    PERFORMANCE: Checks cache first to avoid regenerating embeddings.
    Cache hit rates typically 30-50% in a full pipeline run.

    Args:
        texts: List of text strings

    Returns:
        Numpy array of shape (n_texts, embedding_dim)
    """
    if not texts:
        return np.array([])

    model = get_model()

    # Check cache for embeddings
    cached_embeddings, hit_flags = get_cached_embeddings(texts)

    # Separate cached and non-cached texts
    texts_to_generate = []
    text_indices_to_generate = []

    for i, (text, is_cached) in enumerate(zip(texts, hit_flags)):
        if not is_cached:
            texts_to_generate.append(text)
            text_indices_to_generate.append(i)

    # Generate embeddings only for non-cached texts
    if texts_to_generate:
        generated = model.encode(
            texts_to_generate,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        # Cache the newly generated embeddings
        cache_embeddings(texts_to_generate, generated)

        # Merge cached and newly generated embeddings
        if cached_embeddings is not None and isinstance(cached_embeddings, list):
            for idx, gen_embedding in zip(text_indices_to_generate, generated):
                cached_embeddings[idx] = gen_embedding

            # Extract actual embeddings from cache tuples (embedding, access_time, creation_time)
            embeddings_arr = []
            for item in cached_embeddings:
                if item is None:
                    # This shouldn't happen, but handle it
                    embeddings_arr.append(np.zeros(generated.shape[1]))
                elif isinstance(item, tuple):
                    # New format: (embedding, access_time, creation_time)
                    embeddings_arr.append(item[0])
                else:
                    # Old format or already unwrapped
                    embeddings_arr.append(item)
            return np.array(embeddings_arr)
        else:
            embeddings = np.zeros((len(texts), generated.shape[1]))
            for idx, gen_embedding in zip(text_indices_to_generate, generated):
                embeddings[idx] = gen_embedding
            # Add cached embeddings
            for i, (text, is_cached) in enumerate(zip(texts, hit_flags)):
                if is_cached:
                    # Re-fetch from cache
                    text_hash = str(hash(text))
                    from app.services.embedding_cache import _embedding_cache
                    cached_entry = _embedding_cache[text_hash]
                    # Extract embedding from cache tuple (embedding, access_time, creation_time)
                    if isinstance(cached_entry, tuple):
                        embeddings[i] = cached_entry[0]
                    else:
                        embeddings[i] = cached_entry
            return embeddings
    else:
        # All texts were cached
        if cached_embeddings is None:
            return np.array([])

        # Extract embeddings from cache tuples
        embeddings_arr = []
        for item in cached_embeddings:
            if item is None:
                embeddings_arr.append(None)
            elif isinstance(item, tuple):
                embeddings_arr.append(item[0])
            else:
                embeddings_arr.append(item)

        # Filter out Nones and convert to array
        embeddings_arr = [e for e in embeddings_arr if e is not None]
        return np.array(embeddings_arr) if embeddings_arr else np.array([])


def compute_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Compute cosine similarity between two embeddings.

    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector

    Returns:
        Cosine similarity score (0-1)
    """
    from sklearn.metrics.pairwise import cosine_similarity

    if embedding1.ndim == 1:
        embedding1 = embedding1.reshape(1, -1)
    if embedding2.ndim == 1:
        embedding2 = embedding2.reshape(1, -1)

    return float(cosine_similarity(embedding1, embedding2)[0, 0])
