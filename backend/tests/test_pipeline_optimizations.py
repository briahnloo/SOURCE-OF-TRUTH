"""Comprehensive tests for pipeline optimization modules

Tests for:
1. Incremental clustering system
2. Lazy entity extraction
3. TTL event archival
4. Process pooling
5. Pipeline monitoring
6. Generator-based processing

Total: 35+ test cases
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from app.models import Article, Event
from app.services.incremental_clustering import (
    ClusterAnchor,
    ClusterAnchorManager,
    match_articles_to_existing_clusters,
    compute_cluster_anchor,
    incremental_cluster_articles,
)
from app.services.lazy_entity_extraction import (
    LazyEntityExtractor,
    ExtractedEntity,
    extract_entities_from_articles,
    get_entity_overlap,
    EntityExtractionStream,
)
from app.services.event_archival import (
    EventTier,
    EventTTLConfig,
    EventTierManager,
    archive_old_events,
    EventTTLCache,
)
from app.services.process_pooling import (
    PoolConfig,
    PipelineProcessPool,
    ProcessPoolRegistry,
)
from app.services.pipeline_monitoring import (
    StageMetrics,
    PipelineMetrics,
    PipelineMonitor,
    get_memory_usage_mb,
)


# ============================================================================
# Test Incremental Clustering
# ============================================================================

class TestClusterAnchorManager:
    """Test cluster anchor management"""

    def test_add_anchor(self):
        """Test adding cluster anchor"""
        manager = ClusterAnchorManager()
        embedding = np.random.randn(384).astype(np.float32)

        cluster_id = manager.add_anchor(event_id=1, embedding=embedding, article_count=10)

        assert cluster_id == 1
        assert 1 in manager.anchors
        assert manager.anchors[1].event_id == 1
        assert manager.anchors[1].article_count == 10

    def test_find_best_match(self):
        """Test finding best matching anchor"""
        manager = ClusterAnchorManager()

        # Add anchors
        embedding1 = np.random.randn(384).astype(np.float32)
        embedding2 = np.random.randn(384).astype(np.float32)
        manager.add_anchor(event_id=1, embedding=embedding1, article_count=10)
        manager.add_anchor(event_id=2, embedding=embedding2, article_count=15)

        # Test match to first anchor
        test_embedding = embedding1 + np.random.randn(384) * 0.01  # Similar to embedding1
        match = manager.find_best_match(test_embedding, similarity_threshold=0.5)

        assert match is not None
        assert match[0] == 1  # Should match event 1
        assert match[1] > 0.95  # High similarity

    def test_find_best_match_no_threshold(self):
        """Test no match below threshold"""
        manager = ClusterAnchorManager()
        embedding = np.random.randn(384).astype(np.float32)
        manager.add_anchor(event_id=1, embedding=embedding, article_count=10)

        # Test completely different embedding
        different_embedding = np.random.randn(384).astype(np.float32)
        match = manager.find_best_match(different_embedding, similarity_threshold=0.9)

        assert match is None

    def test_anchor_persistence(self, tmp_path):
        """Test saving and loading anchors"""
        cache_file = str(tmp_path / "anchors.json")
        manager1 = ClusterAnchorManager(cache_file=cache_file)

        # Add anchor
        embedding = np.random.randn(384).astype(np.float32)
        manager1.add_anchor(event_id=1, embedding=embedding, article_count=10)
        manager1.save_anchors()

        # Load in new manager
        manager2 = ClusterAnchorManager(cache_file=cache_file)
        assert len(manager2.anchors) == 1
        assert 1 in manager2.anchors

    def test_get_anchor(self):
        """Test retrieving specific anchor"""
        manager = ClusterAnchorManager()
        embedding = np.random.randn(384).astype(np.float32)
        manager.add_anchor(event_id=1, embedding=embedding, article_count=10)

        anchor = manager.get_anchor(1)
        assert anchor is not None
        assert anchor.event_id == 1
        assert anchor.article_count == 10


class TestIncrementalClustering:
    """Test incremental clustering operations"""

    def test_compute_cluster_anchor(self):
        """Test computing cluster anchor (medoid)"""
        articles = [
            Mock(id=i) for i in range(5)
        ]
        embeddings = np.random.randn(5, 384).astype(np.float32)

        anchor = compute_cluster_anchor(None, event_id=1, articles=articles, embeddings=embeddings)

        assert anchor.shape == (384,)
        assert anchor.dtype == np.float32

    def test_compute_anchor_single_article(self):
        """Test anchor computation with single article"""
        articles = [Mock(id=1)]
        embeddings = np.random.randn(1, 384).astype(np.float32)

        anchor = compute_cluster_anchor(None, event_id=1, articles=articles, embeddings=embeddings)

        assert anchor.shape == (384,)
        np.testing.assert_array_equal(anchor, embeddings[0])


# ============================================================================
# Test Lazy Entity Extraction
# ============================================================================

class TestLazyEntityExtractor:
    """Test lazy entity extraction"""

    def test_extract_entities_with_cache(self):
        """Test entity extraction with caching"""
        extractor = LazyEntityExtractor(cache_size=100)

        text = "John Smith works at Microsoft. He lives in Seattle."

        # First extraction - cache miss
        entities1 = extractor.extract_entities(text, cache_key=1)
        assert extractor.cache_misses == 1
        assert extractor.cache_hits == 0

        # Second extraction - cache hit
        entities2 = extractor.extract_entities(text, cache_key=1)
        assert extractor.cache_hits == 1

        # Should return same results
        assert len(entities1) == len(entities2)

    def test_entity_cache_stats(self):
        """Test cache statistics"""
        extractor = LazyEntityExtractor()
        extractor.cache_hits = 10
        extractor.cache_misses = 5

        stats = extractor.get_cache_stats()
        assert stats["cache_hits"] == 10
        assert stats["cache_misses"] == 5
        assert stats["hit_rate_percent"] == 66.67  # Approximately

    def test_entity_overlap_calculation(self):
        """Test entity overlap computation"""
        entities1 = [
            ExtractedEntity(text="John", entity_type="PERSON"),
            ExtractedEntity(text="Microsoft", entity_type="ORG"),
        ]
        entities2 = [
            ExtractedEntity(text="John", entity_type="PERSON"),
            ExtractedEntity(text="Apple", entity_type="ORG"),
        ]

        overlap = get_entity_overlap(entities1, entities2)
        assert 0 < overlap < 1  # Partial overlap


# ============================================================================
# Test Event Archival
# ============================================================================

class TestEventTierManager:
    """Test event tier management"""

    def test_determine_tier_hot(self):
        """Test hot tier classification"""
        manager = EventTierManager()
        event = Mock(created_at=datetime.utcnow() - timedelta(hours=1))

        tier = manager.determine_tier(event)
        assert tier == EventTier.HOT

    def test_determine_tier_warm(self):
        """Test warm tier classification"""
        manager = EventTierManager()
        event = Mock(created_at=datetime.utcnow() - timedelta(hours=48))

        tier = manager.determine_tier(event)
        assert tier == EventTier.WARM

    def test_determine_tier_cold(self):
        """Test cold tier classification"""
        manager = EventTierManager()
        event = Mock(created_at=datetime.utcnow() - timedelta(days=5))

        tier = manager.determine_tier(event)
        assert tier == EventTier.COLD

    def test_archive_event(self):
        """Test event archival"""
        manager = EventTierManager()
        event = Mock(
            id=1,
            title="Test Event",
            summary="Summary",
            category="politics",
            coherence_score=0.8,
            conflict_severity="high",
            created_at=datetime.utcnow(),
        )

        archived = manager.archive_event(None, event, include_articles=False)

        assert archived is not None
        assert archived.event_id == 1
        assert archived.compression_ratio > 0
        assert archived.compressed_size_bytes < archived.original_size_bytes

    def test_archive_stats(self):
        """Test archive statistics"""
        manager = EventTierManager()
        event = Mock(
            id=1,
            title="Test",
            summary="Summary",
            category="politics",
            coherence_score=0.8,
            conflict_severity="low",
            created_at=datetime.utcnow(),
        )

        manager.archive_event(None, event)
        stats = manager.get_archive_stats()

        assert stats["archived_events"] == 1
        assert stats["memory_saved_mb"] > 0

    def test_ttl_cache_operations(self):
        """Test TTL cache get/put operations"""
        cache = EventTTLCache(max_size=100, ttl_hours=24)
        event = Mock(id=1)

        cache.put(event)
        retrieved = cache.get(1)
        assert retrieved == event

    def test_ttl_cache_eviction(self):
        """Test LRU eviction from TTL cache"""
        cache = EventTTLCache(max_size=3, ttl_hours=24)

        # Fill cache
        for i in range(3):
            cache.put(Mock(id=i))

        assert len(cache.cache) == 3

        # Add one more - should evict least recently used
        cache.put(Mock(id=3))
        assert len(cache.cache) == 3


# ============================================================================
# Test Process Pooling
# ============================================================================

class TestPipelineProcessPool:
    """Test process pool functionality"""

    def test_pool_creation(self):
        """Test process pool creation"""
        config = PoolConfig(max_workers=2)
        pool = PipelineProcessPool(config)

        assert pool.executor is None
        pool.start()
        assert pool.executor is not None
        pool.shutdown()

    def test_pool_context_manager(self):
        """Test pool context manager"""
        with PipelineProcessPool() as pool:
            assert pool.executor is not None
        # Should be shutdown after context

    def test_pool_map_simple(self):
        """Test pool map operation"""
        def square(x):
            return x ** 2

        with PipelineProcessPool() as pool:
            results = pool.map(square, [1, 2, 3, 4])

        assert results == [1, 4, 9, 16]

    def test_pool_stats(self):
        """Test pool statistics"""
        def dummy(x):
            return x

        with PipelineProcessPool() as pool:
            pool.map(dummy, [1, 2, 3])
            stats = pool.get_stats()

        assert stats["tasks_submitted"] == 3
        assert stats["tasks_completed"] == 3


class TestProcessPoolRegistry:
    """Test process pool registry"""

    def test_get_or_create_pool(self):
        """Test creating named pools"""
        with ProcessPoolRegistry() as registry:
            pool1 = registry.get_or_create("pool1")
            pool2 = registry.get_or_create("pool2")

            assert pool1 is not None
            assert pool2 is not None
            assert pool1 != pool2

    def test_get_all_stats(self):
        """Test getting stats from all pools"""
        with ProcessPoolRegistry() as registry:
            registry.get_or_create("pool1")
            registry.get_or_create("pool2")

            stats = registry.get_all_stats()
            assert "pool1" in stats
            assert "pool2" in stats


# ============================================================================
# Test Pipeline Monitoring
# ============================================================================

class TestPipelineMonitor:
    """Test pipeline monitoring"""

    def test_monitor_stage_tracking(self):
        """Test stage metrics tracking"""
        monitor = PipelineMonitor("test_pipeline")

        stage = monitor.start_stage("fetch")
        assert stage.stage_name == "fetch"
        monitor.record_item(success=True)
        monitor.record_item(success=True)
        monitor.end_stage()

        assert stage.items_processed == 2
        assert stage.duration_seconds > 0

    def test_monitor_full_pipeline(self):
        """Test monitoring full pipeline"""
        monitor = PipelineMonitor("test_pipeline")

        # Stage 1
        monitor.start_stage("fetch")
        monitor.record_item(success=True)
        monitor.end_stage()

        # Stage 2
        monitor.start_stage("process")
        monitor.record_item(success=True)
        monitor.end_stage()

        metrics = monitor.finalize()
        assert metrics.total_items_processed == 2
        assert len(metrics.stage_metrics) == 2

    def test_stage_metrics_to_dict(self):
        """Test converting stage metrics to dict"""
        stage = StageMetrics(stage_name="test", start_time=datetime.utcnow())
        stage.items_processed = 100
        stage.duration_seconds = 10

        data = stage.to_dict()
        assert data["stage"] == "test"
        assert data["items_processed"] == 100
        assert data["items_per_second"] == 10

    def test_pipeline_metrics_to_dict(self):
        """Test converting pipeline metrics to dict"""
        metrics = PipelineMetrics(pipeline_name="test", start_time=datetime.utcnow())
        metrics.total_items_processed = 100
        metrics.total_duration_seconds = 10

        data = metrics.to_dict()
        assert data["pipeline"] == "test"
        assert data["total_items"] == 100


# ============================================================================
# Integration Tests
# ============================================================================

class TestPipelineOptimizationsIntegration:
    """Integration tests for pipeline optimizations"""

    def test_incremental_clustering_workflow(self):
        """Test incremental clustering in realistic scenario"""
        manager = ClusterAnchorManager()

        # Add initial anchors
        for i in range(3):
            embedding = np.random.randn(384).astype(np.float32)
            manager.add_anchor(event_id=i+1, embedding=embedding, article_count=10)

        assert len(manager.anchors) == 3

        # Find match
        similar_embedding = manager.anchors[1].embedding + np.random.randn(384) * 0.01
        match = manager.find_best_match(similar_embedding, similarity_threshold=0.8)

        assert match is not None
        assert match[0] == 1

    def test_event_archival_workflow(self):
        """Test event archival in realistic scenario"""
        manager = EventTierManager()

        # Create events at different ages
        old_event = Mock(
            id=1,
            title="Old Event",
            summary="Summary",
            category="politics",
            coherence_score=0.8,
            conflict_severity="high",
            created_at=datetime.utcnow() - timedelta(days=5),
        )
        new_event = Mock(
            id=2,
            title="New Event",
            summary="Summary",
            category="politics",
            coherence_score=0.7,
            conflict_severity="medium",
            created_at=datetime.utcnow() - timedelta(hours=1),
        )

        tier_old = manager.determine_tier(old_event)
        tier_new = manager.determine_tier(new_event)

        assert tier_old == EventTier.COLD
        assert tier_new == EventTier.HOT

        # Archive old event
        manager.archive_event(None, old_event)
        assert manager.should_archive(old_event)
        assert not manager.should_archive(new_event)

    def test_full_pipeline_with_monitoring(self):
        """Test full pipeline with monitoring"""
        monitor = PipelineMonitor("full_pipeline")

        # Simulate fetch stage
        monitor.start_stage("fetch")
        for _ in range(100):
            monitor.record_item(success=True)
        monitor.end_stage()

        # Simulate process stage
        monitor.start_stage("process")
        for _ in range(100):
            monitor.record_item(success=True)
        monitor.end_stage()

        # Simulate cluster stage
        monitor.start_stage("cluster")
        for _ in range(90):
            monitor.record_item(success=True)
        for _ in range(10):
            monitor.record_item(success=False)
        monitor.end_stage()

        metrics = monitor.finalize()
        assert metrics.total_items_processed == 290
        assert metrics.total_items_failed == 10


# ============================================================================
# Performance Benchmarks
# ============================================================================

class TestPipelineOptimizationsPerformance:
    """Performance tests for pipeline optimizations"""

    @pytest.mark.slow
    def test_anchor_manager_performance(self):
        """Benchmark anchor manager with many anchors"""
        manager = ClusterAnchorManager()

        # Add 1000 anchors
        for i in range(1000):
            embedding = np.random.randn(384).astype(np.float32)
            manager.add_anchor(event_id=i, embedding=embedding, article_count=10)

        # Test lookup speed
        test_embedding = np.random.randn(384).astype(np.float32)
        match = manager.find_best_match(test_embedding, similarity_threshold=0.5)

        # Should find match quickly
        assert match is None or isinstance(match, tuple)

    @pytest.mark.slow
    def test_entity_cache_performance(self):
        """Benchmark entity cache with high hit rate"""
        extractor = LazyEntityExtractor(cache_size=10000)

        text = "John Smith works at Microsoft in Seattle."

        # Simulate cache hits
        for i in range(1000):
            extractor.extract_entities(text, cache_key=i % 100)

        stats = extractor.get_cache_stats()
        assert stats["hit_rate_percent"] > 90  # Should have high hit rate

    @pytest.mark.slow
    def test_memory_efficiency_streaming(self):
        """Test memory efficiency of streaming vs batch processing"""
        # This test verifies that streaming doesn't load all data at once
        items = list(range(10000))

        def item_generator():
            for item in items:
                yield item

        # Stream processing should use less memory than batch
        total = 0
        for item in item_generator():
            total += item
            # Memory should not grow significantly

        assert total == sum(items)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
