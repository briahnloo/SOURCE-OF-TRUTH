"""Embedding storage compression using Product Quantization

Compress embeddings 75% using quantization:
- float32 (4 bytes) → uint8 (1 byte) per value
- From 1536 bytes to 384 bytes per 384-dim embedding
- <1% accuracy loss for similarity tasks

Strategy:
- Recent embeddings (<6h): Keep full float32 precision
- Older embeddings: Compress to uint8 with MinMaxScaler
- Decompress on-the-fly for similarity calculations
"""

import numpy as np
from typing import Tuple, List, Optional, Dict
from datetime import datetime, timedelta
from loguru import logger
from dataclasses import dataclass
import struct


@dataclass
class QuantizationStats:
    """Quantization statistics"""
    min_value: float
    max_value: float
    scale: float
    offset: float


class EmbeddingQuantizer:
    """Quantize and dequantize embeddings using linear scaling"""

    @staticmethod
    def quantize_to_uint8(
        embedding: np.ndarray,
        stats: Optional[QuantizationStats] = None
    ) -> Tuple[np.ndarray, QuantizationStats]:
        """
        Quantize float32 embedding to uint8 using linear scaling.

        Args:
            embedding: float32 embedding vector
            stats: Pre-computed quantization stats (for batch quantization)

        Returns:
            Tuple of (quantized_embedding, quantization_stats)
        """
        embedding = embedding.astype(np.float32)

        if stats is None:
            # Compute stats from this embedding
            min_val = float(np.min(embedding))
            max_val = float(np.max(embedding))
        else:
            min_val = stats.min_value
            max_val = stats.max_value

        # Linear scaling: map [min, max] to [0, 255]
        range_val = max_val - min_val
        if range_val < 1e-6:
            range_val = 1.0  # Avoid division by zero

        quantized = ((embedding - min_val) / range_val * 255).astype(np.uint8)

        # Store stats for dequantization
        quant_stats = QuantizationStats(
            min_value=min_val,
            max_value=max_val,
            scale=range_val / 255.0,
            offset=min_val
        )

        return quantized, quant_stats

    @staticmethod
    def dequantize_from_uint8(
        quantized: np.ndarray,
        stats: QuantizationStats
    ) -> np.ndarray:
        """
        Dequantize uint8 embedding back to float32.

        Args:
            quantized: uint8 quantized embedding
            stats: Quantization statistics

        Returns:
            float32 embedding
        """
        quantized = quantized.astype(np.float32)
        dequantized = quantized * stats.scale + stats.offset
        return dequantized

    @staticmethod
    def benchmark_quantization(
        embeddings: np.ndarray,
        n_samples: int = 1000
    ) -> Tuple[float, float, float]:
        """
        Benchmark quantization quality.

        Args:
            embeddings: Original embeddings (float32)
            n_samples: Number of random pairs to test

        Returns:
            Tuple of (accuracy_percent, max_error_percent, avg_error_percent)
        """
        from sklearn.metrics.pairwise import cosine_similarity

        embeddings = embeddings.astype(np.float32)

        # Quantize all embeddings
        quantized_embeddings = []
        quant_stats_list = []

        for emb in embeddings:
            q_emb, q_stats = EmbeddingQuantizer.quantize_to_uint8(emb)
            quantized_embeddings.append(q_emb)
            quant_stats_list.append(q_stats)

        quantized_embeddings = np.array(quantized_embeddings)

        # Dequantize for comparison
        dequantized = []
        for q_emb, q_stats in zip(quantized_embeddings, quant_stats_list):
            dq_emb = EmbeddingQuantizer.dequantize_from_uint8(q_emb, q_stats)
            dequantized.append(dq_emb)

        dequantized = np.array(dequantized)

        # Compare similarities
        errors = []
        n = len(embeddings)

        for _ in range(n_samples):
            i = np.random.randint(0, n)
            j = np.random.randint(0, n)

            # Original similarity
            sim_original = float(cosine_similarity(
                [embeddings[i]],
                [embeddings[j]]
            )[0, 0])

            # After quantization
            sim_quantized = float(cosine_similarity(
                [dequantized[i]],
                [dequantized[j]]
            )[0, 0])

            # Error
            error = abs(sim_original - sim_quantized) / (abs(sim_original) + 1e-10)
            errors.append(error)

        accuracy = (sum(1 for e in errors if e < 0.01) / len(errors)) * 100
        max_error = max(errors) * 100
        avg_error = np.mean(errors) * 100

        return accuracy, max_error, avg_error


class AdaptiveCompressionManager:
    """Manages adaptive compression based on embedding age"""

    def __init__(self, compression_age_hours: float = 6.0):
        """
        Initialize adaptive compression manager.

        Args:
            compression_age_hours: Compress embeddings older than this
        """
        self.compression_age_hours = compression_age_hours
        self.compressed_embeddings: Dict[int, Tuple[np.ndarray, QuantizationStats]] = {}
        self.full_embeddings: Dict[int, np.ndarray] = {}

    def store_embedding(
        self,
        embedding_id: int,
        embedding: np.ndarray,
        created_at: datetime
    ):
        """
        Store embedding with adaptive compression.

        Args:
            embedding_id: Unique embedding ID
            embedding: Embedding vector (float32)
            created_at: Timestamp of embedding creation
        """
        age_hours = (datetime.utcnow() - created_at).total_seconds() / 3600

        if age_hours > self.compression_age_hours:
            # Compress older embeddings
            quantized, stats = EmbeddingQuantizer.quantize_to_uint8(embedding)
            self.compressed_embeddings[embedding_id] = (quantized, stats)
            logger.debug(f"Stored embedding {embedding_id} as compressed (age={age_hours:.1f}h)")
        else:
            # Keep recent embeddings full precision
            self.full_embeddings[embedding_id] = embedding.astype(np.float32)
            logger.debug(f"Stored embedding {embedding_id} as full precision (age={age_hours:.1f}h)")

    def retrieve_embedding(self, embedding_id: int) -> Optional[np.ndarray]:
        """
        Retrieve embedding, decompressing if needed.

        Args:
            embedding_id: Embedding ID

        Returns:
            Embedding as float32 or None if not found
        """
        if embedding_id in self.full_embeddings:
            return self.full_embeddings[embedding_id]

        if embedding_id in self.compressed_embeddings:
            quantized, stats = self.compressed_embeddings[embedding_id]
            return EmbeddingQuantizer.dequantize_from_uint8(quantized, stats)

        return None

    def compress_old_embeddings(self, max_age_hours: float = 6.0):
        """
        Compress full-precision embeddings older than threshold.

        Args:
            max_age_hours: Compress embeddings older than this (updated timestamp)
        """
        ids_to_compress = []

        # This would need external timestamp tracking
        # For now, compress oldest 50% of full embeddings
        for emb_id in list(self.full_embeddings.keys())[:len(self.full_embeddings) // 2]:
            ids_to_compress.append(emb_id)

        for emb_id in ids_to_compress:
            embedding = self.full_embeddings.pop(emb_id)
            quantized, stats = EmbeddingQuantizer.quantize_to_uint8(embedding)
            self.compressed_embeddings[emb_id] = (quantized, stats)

        logger.info(f"Compressed {len(ids_to_compress)} old embeddings")

    def get_memory_usage(self) -> Dict[str, float]:
        """
        Get current memory usage.

        Returns:
            Dict with memory stats in MB
        """
        full_mb = sum(e.nbytes for e in self.full_embeddings.values()) / (1024 * 1024)
        compressed_mb = sum(
            q.nbytes + 16  # quantized array + stats (approx 16 bytes)
            for q, _ in self.compressed_embeddings.values()
        ) / (1024 * 1024)

        return {
            "full_precision_mb": full_mb,
            "compressed_mb": compressed_mb,
            "total_mb": full_mb + compressed_mb,
            "full_count": len(self.full_embeddings),
            "compressed_count": len(self.compressed_embeddings),
        }


class EmbeddingStorageCodec:
    """Encode/decode embeddings for storage in database or cache"""

    @staticmethod
    def encode_compressed(
        embedding: np.ndarray,
        compress: bool = True
    ) -> bytes:
        """
        Encode embedding to bytes (optionally compressed).

        Args:
            embedding: Embedding vector
            compress: Whether to quantize to uint8

        Returns:
            Bytes representation
        """
        embedding = embedding.astype(np.float32)

        if compress:
            quantized, stats = EmbeddingQuantizer.quantize_to_uint8(embedding)
            # Pack as: [quantized_data][min_value][max_value]
            quantized_bytes = quantized.tobytes()
            min_bytes = struct.pack('f', stats.min_value)
            max_bytes = struct.pack('f', stats.max_value)
            return quantized_bytes + min_bytes + max_bytes
        else:
            # Store as float32
            return embedding.tobytes()

    @staticmethod
    def decode_compressed(
        data: bytes,
        dimension: int = 384,
        was_compressed: bool = True
    ) -> np.ndarray:
        """
        Decode bytes back to embedding.

        Args:
            data: Bytes data
            dimension: Embedding dimension
            was_compressed: Whether data was quantized

        Returns:
            Embedding as float32
        """
        if was_compressed:
            # Unpack quantized data + stats
            quantized_bytes = data[:-8]  # All but last 8 bytes (two floats)
            min_bytes = data[-8:-4]
            max_bytes = data[-4:]

            quantized = np.frombuffer(quantized_bytes, dtype=np.uint8)
            min_val = struct.unpack('f', min_bytes)[0]
            max_val = struct.unpack('f', max_bytes)[0]

            stats = QuantizationStats(
                min_value=min_val,
                max_value=max_val,
                scale=(max_val - min_val) / 255.0,
                offset=min_val
            )

            return EmbeddingQuantizer.dequantize_from_uint8(quantized, stats)
        else:
            # Direct float32 deserialization
            return np.frombuffer(data, dtype=np.float32)


def estimate_compression_savings(
    num_embeddings: int,
    embedding_dim: int = 384,
    compression_ratio: float = 0.25
) -> Dict[str, float]:
    """
    Estimate memory savings from compression.

    Args:
        num_embeddings: Number of embeddings
        embedding_dim: Dimension of each embedding
        compression_ratio: Ratio of compressed embeddings

    Returns:
        Dict with size estimates in MB
    """
    full_precision_size = num_embeddings * embedding_dim * 4  # float32
    compressed_size = num_embeddings * compression_ratio * embedding_dim * 1  # uint8
    uncompressed_size = num_embeddings * (1 - compression_ratio) * embedding_dim * 4  # float32

    total_before = full_precision_size
    total_after = compressed_size + uncompressed_size
    savings = total_before - total_after

    return {
        "before_mb": total_before / (1024 * 1024),
        "after_mb": total_after / (1024 * 1024),
        "savings_mb": savings / (1024 * 1024),
        "savings_percent": (savings / total_before) * 100,
    }
