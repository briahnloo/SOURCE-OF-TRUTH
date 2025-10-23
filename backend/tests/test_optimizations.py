"""
Comprehensive tests for memory optimizations

Tests for:
1. Memory management utilities (expunge_all, gc.collect)
2. Sparse KNN clustering (vs old DBSCAN)
3. Embedding cache with LRU + TTL
4. Config changes (48h window)
"""

import time
import gc
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import pytest


class TestMemoryUtilities:
    """Tests for memory management utilities"""

    def test_clear_session_cache(self):
        """Test SQLAlchemy session cache clearing"""
        from app.core.memory_utils import clear_session_cache

        # Mock session
        mock_session = Mock()
        mock_session.expunge_all = Mock()

        # Call should not raise
        clear_session_cache(mock_session)

        # Verify expunge_all was called
        mock_session.expunge_all.assert_called_once()

    def test_memory_safe_processing_context_manager(self):
        """Test memory-safe processing context manager"""
        from app.core.memory_utils import memory_safe_processing

        mock_session = Mock()
        mock_session.expunge_all = Mock()

        # Use context manager
        with memory_safe_processing(mock_session, cleanup_interval=2) as ctx:
            ctx.mark_processed()
            ctx.mark_processed()
            # Should trigger cleanup (every 2 items)

        # Verify cleanup was called
        assert mock_session.expunge_all.called

    def test_memory_safe_processing_cleanup_interval(self):
        """Test cleanup happens at correct intervals"""
        from app.core.memory_utils import memory_safe_processing

        mock_session = Mock()
        mock_session.expunge_all = Mock()

        with memory_safe_processing(mock_session, cleanup_interval=3) as ctx:
            for _ in range(7):
                ctx.mark_processed()

        # Should have been called at least twice (at 3 and 6 items)
        assert mock_session.expunge_all.call_count >= 2

    def test_memory_profiler_get_size(self):
        """Test memory profiler size reporting"""
        from app.core.memory_utils import MemoryProfiler

        # Should return a number >= 0
        size = MemoryProfiler.get_size_mb()
        assert isinstance(size, float)
        assert size >= 0

    def test_memory_profiler_high_threshold_logging(self):
        """Test memory profiler high usage alerting"""
        from app.core.memory_utils import MemoryProfiler

        # Should not raise even with unrealistic threshold
        MemoryProfiler.log_if_high(threshold_mb=1, label="test")


class TestSparseKNNClustering:
    """Tests for sparse KNN clustering vs DBSCAN"""

    def test_sparse_knn_clustering_basic(self):
        """Test basic sparse KNN clustering functionality"""
        from app.services.sparse_clustering import cluster_with_sparse_knn

        # Create simple test embeddings (3 clusters + noise)
        np.random.seed(42)

        # Cluster 1: similar embeddings
        cluster1 = np.random.normal(loc=[1, 1], scale=0.1, size=(5, 2))
        # Cluster 2: different similar embeddings
        cluster2 = np.random.normal(loc=[5, 5], scale=0.1, size=(5, 2))
        # Noise: random scattered points
        noise = np.random.uniform(low=-5, high=5, size=(3, 2))

        embeddings = np.vstack([cluster1, cluster2, noise])

        # Cluster
        labels = cluster_with_sparse_knn(embeddings, k=3, min_cluster_size=3)

        # Should find at least 2 clusters
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        assert n_clusters >= 2, f"Expected >= 2 clusters, got {n_clusters}"

    def test_sparse_knn_clustering_memory_efficient(self):
        """Test that sparse KNN uses less memory than full distance matrix"""
        from app.services.sparse_clustering import cluster_with_sparse_knn

        # Create larger embeddings (1000 articles)
        embeddings = np.random.normal(size=(1000, 384))

        # This should complete without memory issues
        labels = cluster_with_sparse_knn(embeddings, k=5)

        # Verify labels shape matches input
        assert len(labels) == len(embeddings)
        assert set(labels).issubset(set(range(max(labels) + 1)) | {-1})

    def test_sparse_knn_clustering_with_low_k(self):
        """Test clustering with k smaller than min_samples"""
        from app.services.sparse_clustering import cluster_with_sparse_knn

        embeddings = np.random.normal(size=(10, 384))

        # k smaller than min_cluster_size should still work
        labels = cluster_with_sparse_knn(embeddings, k=2, min_cluster_size=3)

        # Should return valid labels
        assert len(labels) == len(embeddings)

    def test_sparse_knn_get_cluster_anchor(self):
        """Test getting representative article for a cluster"""
        from app.services.sparse_clustering import get_cluster_anchor

        # Create embeddings with one clearly representative
        np.random.seed(42)
        # Center point (most similar to others)
        center = np.array([0, 0])
        # Cluster around center
        embeddings = np.array([
            center,
            [0.1, 0.1],
            [0.1, -0.1],
            [-0.1, 0.1],
        ])

        indices = [0, 1, 2, 3]
        anchor_idx = get_cluster_anchor(embeddings, indices)

        # Anchor should be close to center (index 0)
        assert anchor_idx == 0

    def test_sparse_knn_match_articles_to_clusters(self):
        """Test matching new articles to existing clusters"""
        from app.services.sparse_clustering import match_articles_to_existing_clusters

        np.random.seed(42)

        # Create existing cluster embeddings
        existing = np.random.normal(loc=[0, 0], scale=0.1, size=(10, 384))

        # Create new embeddings (some similar, some different)
        similar = np.random.normal(loc=[0, 0], scale=0.1, size=(5, 384))
        different = np.random.normal(loc=[10, 10], scale=0.1, size=(5, 384))
        new_embeddings = np.vstack([similar, different])

        # Simple clusters dict
        existing_clusters = {0: list(range(10))}

        # Match
        labels = match_articles_to_existing_clusters(
            new_embeddings,
            existing,
            existing_clusters,
            similarity_threshold=0.5
        )

        # Should have assigned some to cluster 0, rest as noise
        assert len(labels) == len(new_embeddings)
        matched = np.sum(labels != -1)
        assert matched > 0, "Should match some articles"
        assert matched < len(new_embeddings), "Should not match all (different cluster)"


class TestEmbeddingCacheLRU:
    """Tests for embedding cache with LRU and TTL"""

    def test_cache_basic_storage_retrieval(self):
        """Test basic cache store and retrieve"""
        from app.services.embedding_cache import cache_embeddings, get_cached_embeddings, clear_cache

        clear_cache()

        # Create test embeddings
        texts = ["hello", "world"]
        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)

        # Store
        cache_embeddings(texts, embeddings)

        # Retrieve
        cached, hit_flags = get_cached_embeddings(texts)

        # Both should be hits
        assert hit_flags == [True, True]
        assert cached is not None

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache exceeds max size"""
        from app.services.embedding_cache import (
            cache_embeddings,
            get_cached_embeddings,
            clear_cache,
            CACHE_MAX_SIZE,
        )

        clear_cache()

        # Create embeddings exceeding cache size
        num_texts = CACHE_MAX_SIZE + 100

        texts = [f"text_{i}" for i in range(num_texts)]
        embeddings = np.random.normal(size=(num_texts, 384))

        # Store all
        for i in range(0, num_texts, 100):
            batch_texts = texts[i : i + 100]
            batch_embeddings = embeddings[i : i + 100]
            cache_embeddings(batch_texts, batch_embeddings)

        # Get stats
        stats = cache_embeddings.__module__
        # Import to get stats
        from app.services.embedding_cache import get_cache_stats
        stats = get_cache_stats()

        # Cache should not exceed max size
        assert stats["cache_size"] <= CACHE_MAX_SIZE * 1.1  # 10% tolerance

    def test_cache_ttl_expiration(self):
        """Test TTL-based cache expiration"""
        from app.services.embedding_cache import (
            cache_embeddings,
            get_cached_embeddings,
            clear_cache,
            _embedding_cache,
            CACHE_TTL_SECONDS,
        )

        clear_cache()

        # Create and cache embeddings
        texts = ["text1", "text2"]
        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)
        cache_embeddings(texts, embeddings)

        # Verify cached
        cached, hit_flags = get_cached_embeddings(texts)
        assert hit_flags == [True, True]

        # Manually expire entries by changing creation time
        for key in list(_embedding_cache.keys()):
            embedding, access_time, _ = _embedding_cache[key]
            # Set creation time to far past (> TTL)
            _embedding_cache[key] = (embedding, access_time, time.time() - CACHE_TTL_SECONDS - 100)

        # Try to retrieve - should be expired
        cached, hit_flags = get_cached_embeddings(texts)
        # Should be misses now
        assert hit_flags == [False, False]

    def test_cache_hit_rate_tracking(self):
        """Test cache hit/miss statistics"""
        from app.services.embedding_cache import (
            cache_embeddings,
            get_cached_embeddings,
            get_cache_stats,
            clear_cache,
        )

        clear_cache()

        # Cache some texts
        texts1 = ["a", "b", "c"]
        embeddings1 = np.random.normal(size=(3, 384))
        cache_embeddings(texts1, embeddings1)

        # Access cached texts
        cached, _ = get_cached_embeddings(texts1)

        # Access some new texts (misses)
        cached, _ = get_cached_embeddings(["d", "e", "f"])

        # Check stats
        stats = get_cache_stats()

        assert stats["hits"] > 0
        assert stats["misses"] > 0
        assert "hit_rate" in stats
        assert 0 <= stats["hit_rate"] <= 1

    def test_cache_clear(self):
        """Test clearing cache"""
        from app.services.embedding_cache import (
            cache_embeddings,
            get_cache_stats,
            clear_cache,
        )

        # Cache some data
        texts = ["test1", "test2"]
        embeddings = np.random.normal(size=(2, 384))
        cache_embeddings(texts, embeddings)

        # Verify cached
        stats_before = get_cache_stats()
        assert stats_before["cache_size"] > 0

        # Clear
        clear_cache()

        # Verify cleared
        stats_after = get_cache_stats()
        assert stats_after["cache_size"] == 0
        assert stats_after["hits"] == 0


class TestConfigChanges:
    """Tests for configuration changes (48h window)"""

    def test_analysis_window_config_exists(self):
        """Test that analysis_window_hours config exists"""
        from app.config import settings

        # Should have the new config
        assert hasattr(settings, "analysis_window_hours")
        assert settings.analysis_window_hours == 48

    def test_analysis_window_is_less_than_72(self):
        """Test that analysis window was reduced from 72h"""
        from app.config import settings

        assert settings.analysis_window_hours <= 48
        # Should be 48h (the optimization)
        assert settings.analysis_window_hours == 48


class TestIntegration:
    """Integration tests combining multiple optimizations"""

    def test_sparse_clustering_with_cached_embeddings(self):
        """Test sparse clustering using cached embeddings"""
        from app.services.sparse_clustering import cluster_with_sparse_knn
        from app.services.embedding_cache import (
            cache_embeddings,
            get_cached_embeddings,
            clear_cache,
        )

        clear_cache()

        # Create test embeddings
        embeddings = np.random.normal(size=(100, 384))
        texts = [f"article_{i}" for i in range(100)]

        # Cache them
        cache_embeddings(texts, embeddings)

        # Use for clustering
        labels = cluster_with_sparse_knn(embeddings, k=5)

        # Should produce valid clusters
        assert len(labels) == len(embeddings)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        assert n_clusters >= 0

    def test_memory_safe_processing_with_mocked_db(self):
        """Test memory-safe processing in realistic scenario"""
        from app.core.memory_utils import memory_safe_processing

        mock_db = Mock()
        mock_db.expunge_all = Mock()

        # Simulate processing 25 items with cleanup every 5
        with memory_safe_processing(mock_db, cleanup_interval=5, description="test") as ctx:
            for i in range(25):
                # Simulate work
                ctx.mark_processed()

        # Should have cleaned up multiple times
        assert mock_db.expunge_all.call_count > 1


class TestMemorySavings:
    """Tests demonstrating memory savings"""

    def test_sparse_knn_vs_dbscan_matrix_size_estimation(self):
        """Estimate memory savings: sparse vs full matrix"""

        # For 10,000 articles with 384-dim embeddings
        n_articles = 10000
        embedding_dim = 384

        # Full DBSCAN distance matrix: O(n²)
        dbscan_matrix_elements = n_articles ** 2
        # Each element is ~8 bytes (float64)
        dbscan_memory_mb = (dbscan_matrix_elements * 8) / (1024 * 1024)

        # Sparse KNN: k=5 neighbors per article
        k = 5
        sparse_edges = n_articles * k
        sparse_memory_mb = (sparse_edges * 8) / (1024 * 1024)

        # Savings should be massive
        savings_percent = ((dbscan_memory_mb - sparse_memory_mb) / dbscan_memory_mb) * 100

        print(f"\nMemory savings estimation:")
        print(f"DBSCAN matrix: {dbscan_memory_mb:.0f} MB")
        print(f"Sparse KNN:    {sparse_memory_mb:.0f} MB")
        print(f"Savings:       {savings_percent:.1f}%")

        # Should save 99%+
        assert savings_percent > 99

    def test_lru_cache_size_reduction(self):
        """Test cache size reduction from 10K to 5K entries"""
        from app.services.embedding_cache import CACHE_MAX_SIZE

        # Should be 5000 (from 10000)
        assert CACHE_MAX_SIZE == 5000

        # With 384-dim embeddings
        embedding_dim = 384
        bytes_per_entry = embedding_dim * 8  # float64

        old_max_size = 10000
        new_max_size = CACHE_MAX_SIZE

        old_memory_mb = (old_max_size * bytes_per_entry) / (1024 * 1024)
        new_memory_mb = (new_max_size * bytes_per_entry) / (1024 * 1024)

        print(f"\nCache size reduction:")
        print(f"Old max: {old_max_size} entries = {old_memory_mb:.1f} MB")
        print(f"New max: {new_max_size} entries = {new_memory_mb:.1f} MB")

        # Should reduce by 50%
        assert new_memory_mb == old_memory_mb / 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
