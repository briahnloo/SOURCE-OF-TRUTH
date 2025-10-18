"""Embedding generation using sentence-transformers"""

from typing import List

import numpy as np
from app.config import settings
from sentence_transformers import SentenceTransformer

# Lazy load model
_model = None


def get_model() -> SentenceTransformer:
    """Lazy load sentence-transformers model"""
    global _model
    if _model is None:
        print(f"Loading embedding model: {settings.embedding_model}")
        _model = SentenceTransformer(settings.embedding_model)
        print("✅ Embedding model loaded")
    return _model


def generate_embeddings(texts: List[str]) -> np.ndarray:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings

    Returns:
        Numpy array of shape (n_texts, embedding_dim)
    """
    if not texts:
        return np.array([])

    model = get_model()

    # Generate embeddings in batches
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
    )

    return embeddings


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
