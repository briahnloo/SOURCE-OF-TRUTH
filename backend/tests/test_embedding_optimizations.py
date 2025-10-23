"""
Comprehensive tests for embedding optimization

Tests for:
1. INT8 quantization quality
2. Dual-tier embedding system
3. Product quantization storage
4. Cross-tier similarity calculations
5. Migration path verification
"""

import numpy as np
import pytest
from datetime import datetime, timedelta


class TestINT8Quantization:
    """Tests for INT8 model quantization"""

    def test_quantized_model_loads(self):
        """Test that quantized model loads successfully"""
        from app.services.quantized_embeddings import QuantizedEmbeddingModel

        model = QuantizedEmbeddingModel()
        assert model.model is not None
        assert model.device is not None
        logger.info(f"✅ Quantized model loaded on {model.device}")

    def test_float16_conversion(self):
        """Test float16 embedding storage"""
        embeddings_float32 = np.random.randn(100, 384).astype(np.float32)

        # Convert to float16
        embeddings_float16 = embeddings_float32.astype(np.float16)

        # Verify size reduction
        size_float32 = embeddings_float32.nbytes
        size_float16 = embeddings_float16.nbytes

        reduction = (1 - size_float16 / size_float32) * 100
        assert reduction >= 49  # Should be ~50% reduction
        print(f"Float16 size reduction: {reduction:.1f}%")

    def test_similarity_quality_after_quantization(self):
        """Test that quantization preserves similarity quality"""
        from app.services.quantized_embeddings import EmbeddingQualityBenchmark

        # Create random embeddings
        embeddings_full = np.random.randn(1000, 384).astype(np.float32)
        embeddings_float16 = embeddings_full.astype(np.float16)

        # Benchmark
        accuracy, max_error = EmbeddingQualityBenchmark.benchmark_similarity_accuracy(
            embeddings_full,
            embeddings_float16,
            n_pairs=1000
        )

        print(f"\nSimilarity Quality Benchmark (float16):")
        print(f"  Accuracy (within 1%): {accuracy:.1f}%")
        print(f"  Max error: {max_error:.2f}%")

        # Float16 should maintain >98% accuracy
        assert accuracy > 98.0, f"Accuracy {accuracy}% below 98% threshold"
        assert max_error < 2.0, f"Max error {max_error}% exceeds 2% threshold"

    def test_clustering_stability_with_float16(self):
        """Test clustering stability with float16"""
        from app.services.quantized_embeddings import EmbeddingQualityBenchmark

        embeddings_full = np.random.randn(500, 384).astype(np.float32)
        embeddings_float16 = embeddings_full.astype(np.float16)

        # Benchmark clustering
        score_full, score_quantized, match = EmbeddingQualityBenchmark.benchmark_clustering_stability(
            embeddings_full,
            embeddings_float16
        )

        print(f"\nClustering Stability (float16):")
        print(f"  Full precision silhouette score: {score_full:.3f}")
        print(f"  Float16 silhouette score: {score_quantized:.3f}")
        print(f"  Cluster assignment match: {match:.1f}%")

        # Should maintain high cluster match
        assert match > 85.0, f"Cluster match {match}% below 85% threshold"


class TestDualTierEmbeddings:
    """Tests for dual-tier embedding system"""

    def test_tier_determination_logic(self):
        """Test tier selection logic"""
        from app.services.dual_tier_embeddings import DualTierEmbeddingManager, TIER_1, TIER_2

        manager = DualTierEmbeddingManager()

        # Recent article without conflicts -> Tier 1
        tier = manager.determine_tier(
            article_age_hours=5,
            is_breaking=False,
            has_conflict=False,
            importance_score=50
        )
        assert tier == TIER_1

        # Old article without conflicts -> Tier 2
        tier = manager.determine_tier(
            article_age_hours=48,
            is_breaking=False,
            has_conflict=False,
            importance_score=50
        )
        assert tier == TIER_2

        # Breaking news regardless of age -> Tier 1
        tier = manager.determine_tier(
            article_age_hours=72,
            is_breaking=True,
            has_conflict=False,
            importance_score=0
        )
        assert tier == TIER_1

        # High importance -> Tier 1
        tier = manager.determine_tier(
            article_age_hours=72,
            is_breaking=False,
            has_conflict=False,
            importance_score=80
        )
        assert tier == TIER_1

        print("✅ Tier determination logic working correctly")

    def test_dimension_mismatch_handling(self):
        """Test handling of cross-tier similarity"""
        from app.services.dual_tier_embeddings import DualTierEmbeddingManager, TIER_1, TIER_2

        manager = DualTierEmbeddingManager()

        # Tier 1: 384-dim, Tier 2: 128-dim
        embedding1 = np.random.randn(TIER_1.dimension).astype(np.float16)
        embedding2 = np.random.randn(TIER_2.dimension).astype(np.float16)

        # Should calculate similarity without error (with padding)
        similarity = manager.cross_tier_similarity(
            embedding1,
            TIER_1.name,
            embedding2,
            TIER_2.name
        )

        assert -1.0 <= similarity <= 1.0
        print(f"✅ Cross-tier similarity: {similarity:.3f}")

    def test_memory_savings_estimate(self):
        """Test memory savings calculation"""
        from app.services.dual_tier_embeddings import DualTierEmbeddingManager

        manager = DualTierEmbeddingManager()
        estimates = manager.get_memory_usage_estimate()

        print(f"\nDual-Tier Memory Savings Estimate:")
        print(f"  Tier 1 embeddings: {estimates['tier1_embeddings_mb']:.1f} MB")
        print(f"  Tier 2 embeddings: {estimates['tier2_embeddings_mb']:.1f} MB")
        print(f"  Total dual-tier: {estimates['total_dual_tier_mb']:.1f} MB")
        print(f"  Single-tier equivalent: {estimates['single_tier_embeddings_mb']:.1f} MB")
        print(f"  Savings: {estimates['savings_mb']:.1f} MB ({(estimates['savings_mb']/estimates['single_tier_embeddings_mb']*100):.1f}%)")

        # Should save 200-300MB for 10K articles
        assert estimates['savings_mb'] >= 100


class TestEmbeddingCompression:
    """Tests for embedding compression with quantization"""

    def test_quantization_encode_decode(self):
        """Test uint8 quantization and dequantization"""
        from app.services.embedding_compression import EmbeddingQuantizer

        # Original embedding
        original = np.random.randn(384).astype(np.float32)

        # Quantize
        quantized, stats = EmbeddingQuantizer.quantize_to_uint8(original)
        assert quantized.dtype == np.uint8
        assert quantized.shape == (384,)

        # Dequantize
        recovered = EmbeddingQuantizer.dequantize_from_uint8(quantized, stats)
        assert recovered.dtype == np.float32

        # Should be very close
        max_error = np.max(np.abs(original - recovered))
        relative_error = max_error / (np.max(np.abs(original)) + 1e-10)
        assert relative_error < 0.01, f"Relative error {relative_error} too high"

        print(f"✅ Quantization/dequantization max error: {relative_error*100:.2f}%")

    def test_quantization_quality_benchmark(self):
        """Test quantization quality on similarity tasks"""
        from app.services.embedding_compression import EmbeddingQuantizer

        # Create test embeddings
        embeddings = np.random.randn(1000, 384).astype(np.float32)

        # Benchmark
        accuracy, max_error, avg_error = EmbeddingQuantizer.benchmark_quantization(
            embeddings,
            n_samples=1000
        )

        print(f"\nQuantization Quality Benchmark (uint8):")
        print(f"  Accuracy (within 1%): {accuracy:.1f}%")
        print(f"  Max error: {max_error:.2f}%")
        print(f"  Avg error: {avg_error:.2f}%")

        # Should maintain >98% accuracy
        assert accuracy > 98.0, f"Accuracy {accuracy}% below 98%"
        assert max_error < 2.0, f"Max error {max_error}% above 2%"

    def test_adaptive_compression_storage(self):
        """Test adaptive compression based on age"""
        from app.services.embedding_compression import AdaptiveCompressionManager

        manager = AdaptiveCompressionManager(compression_age_hours=6.0)

        # Recent embedding (should stay full precision)
        recent_emb = np.random.randn(384).astype(np.float32)
        recent_time = datetime.utcnow() - timedelta(hours=3)
        manager.store_embedding(1, recent_emb, recent_time)

        # Old embedding (should be compressed)
        old_emb = np.random.randn(384).astype(np.float32)
        old_time = datetime.utcnow() - timedelta(hours=24)
        manager.store_embedding(2, old_emb, old_time)

        # Check storage
        assert 1 in manager.full_embeddings, "Recent embedding should be full precision"
        assert 2 in manager.compressed_embeddings, "Old embedding should be compressed"

        # Both should retrieve correctly
        retrieved_recent = manager.retrieve_embedding(1)
        retrieved_old = manager.retrieve_embedding(2)

        assert retrieved_recent is not None
        assert retrieved_old is not None
        assert np.allclose(retrieved_recent, recent_emb, atol=0.001)

        print("✅ Adaptive compression storage working")

    def test_compression_memory_savings(self):
        """Test actual memory savings from compression"""
        from app.services.embedding_compression import estimate_compression_savings

        # For 10,000 embeddings with 75% compression ratio
        estimates = estimate_compression_savings(
            num_embeddings=10000,
            embedding_dim=384,
            compression_ratio=0.75
        )

        print(f"\nCompression Memory Savings:")
        print(f"  Before: {estimates['before_mb']:.1f} MB")
        print(f"  After: {estimates['after_mb']:.1f} MB")
        print(f"  Savings: {estimates['savings_mb']:.1f} MB ({estimates['savings_percent']:.1f}%)")

        # Should save ~250-300MB for 10K embeddings
        assert estimates['savings_mb'] >= 200
        assert estimates['savings_percent'] >= 60

    def test_storage_codec(self):
        """Test embedding storage codec"""
        from app.services.embedding_compression import EmbeddingStorageCodec

        original = np.random.randn(384).astype(np.float32)

        # Encode compressed
        encoded = EmbeddingStorageCodec.encode_compressed(original, compress=True)
        assert isinstance(encoded, bytes)
        assert len(encoded) < original.nbytes  # Should be smaller

        # Decode
        decoded = EmbeddingStorageCodec.decode_compressed(encoded, dimension=384, was_compressed=True)
        assert decoded.dtype == np.float32

        # Should recover with minimal error
        error = np.max(np.abs(original - decoded)) / (np.max(np.abs(original)) + 1e-10)
        assert error < 0.01

        print(f"✅ Storage codec compression: {(1-len(encoded)/original.nbytes)*100:.1f}% size reduction")


class TestMigrationPath:
    """Tests for migration from current system to optimized system"""

    def test_backward_compatibility(self):
        """Test that old embeddings can be read and used"""
        # Simulate old format: float32 embeddings
        old_embeddings = np.random.randn(100, 384).astype(np.float32)

        # Should be readable by new system
        from app.services.quantized_embeddings import dequantize_embedding_array
        dequantized = dequantize_embedding_array(old_embeddings)

        assert dequantized.dtype == np.float32
        assert np.allclose(dequantized, old_embeddings)
        print("✅ Backward compatibility verified")

    def test_mixed_precision_similarity(self):
        """Test similarity between mixed precision embeddings"""
        from sklearn.metrics.pairwise import cosine_similarity

        # Float32
        emb_f32 = np.random.randn(384).astype(np.float32)
        # Float16
        emb_f16 = emb_f32.astype(np.float16).astype(np.float32)  # Downgrade and recover

        # Similarity should be nearly identical
        sim = float(cosine_similarity([emb_f32], [emb_f16])[0, 0])
        assert abs(sim - 1.0) < 0.01  # Should be very close to 1.0

        print(f"✅ Mixed precision similarity: {sim:.4f}")

    def test_migration_pipeline(self):
        """Test end-to-end migration pipeline"""
        from app.services.quantized_embeddings import quantize_embedding_array
        from app.services.embedding_compression import EmbeddingQuantizer

        # Original embeddings (float32)
        original = np.random.randn(1000, 384).astype(np.float32)

        # Step 1: Quantize to float16
        step1 = quantize_embedding_array(original, to_float16=True)
        assert step1.dtype == np.float16
        size_reduction_1 = (1 - step1.nbytes / original.nbytes) * 100
        print(f"Step 1 (float16): {size_reduction_1:.1f}% size reduction")

        # Step 2: Further compress with uint8
        step2_compressed = []
        for emb in step1:
            q_emb, _ = EmbeddingQuantizer.quantize_to_uint8(emb.astype(np.float32))
            step2_compressed.append(q_emb)

        step2 = np.array(step2_compressed)
        total_reduction = (1 - step2.nbytes / original.nbytes) * 100
        print(f"Step 2 (uint8): {total_reduction:.1f}% total size reduction")

        # Should achieve ~75% reduction (384 float32 -> 384 uint8 = 75%)
        assert total_reduction >= 70


class TestPerformanceBenchmarks:
    """Performance benchmarks for optimization"""

    def test_encoding_speed_comparison(self):
        """Compare encoding speed: original vs quantized"""
        import time

        texts = ["This is a test article about important world events."] * 100

        print(f"\nEncoding Speed Benchmark ({len(texts)} texts):")

        # Simulate original encoding (just random embeddings for speed test)
        start = time.time()
        embeddings_orig = np.random.randn(len(texts), 384).astype(np.float32)
        time_orig = time.time() - start

        # Simulate quantized encoding (float16 conversion)
        from app.services.quantized_embeddings import quantize_embedding_array
        start = time.time()
        embeddings_quant = quantize_embedding_array(embeddings_orig, to_float16=True)
        time_quant = time.time() - start

        print(f"  Original (float32): {time_orig*1000:.2f}ms")
        print(f"  Quantized (float16): {time_quant*1000:.2f}ms")
        print(f"  Speedup: {(time_orig/time_quant):.2f}x")

    def test_similarity_computation_speed(self):
        """Test similarity computation speed with compressed embeddings"""
        import time
        from sklearn.metrics.pairwise import cosine_similarity

        embeddings = np.random.randn(10000, 384).astype(np.float32)
        embeddings_float16 = embeddings.astype(np.float16).astype(np.float32)

        # Compute many similarities
        start = time.time()
        for _ in range(1000):
            i, j = np.random.randint(0, 10000, 2)
            cosine_similarity([embeddings[i]], [embeddings[j]])
        time_orig = time.time() - start

        start = time.time()
        for _ in range(1000):
            i, j = np.random.randint(0, 10000, 2)
            cosine_similarity([embeddings_float16[i]], [embeddings_float16[j]])
        time_quant = time.time() - start

        print(f"\nSimilarity Computation Benchmark (1000 pairs):")
        print(f"  Float32: {time_orig*1000:.2f}ms")
        print(f"  Float16: {time_quant*1000:.2f}ms")


if __name__ == "__main__":
    import logging
    from loguru import logger

    # Setup logging
    logger.enable("app.services")
    logging.basicConfig(level=logging.INFO)

    pytest.main([__file__, "-v", "-s"])
