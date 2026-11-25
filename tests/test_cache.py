import tempfile
from pathlib import Path
from unittest import TestCase, mock
import time

from src import cache


class TestCache(TestCase):
    """Test suite for the cache module."""

    def setUp(self) -> None:
        self.temp_cache_dir = tempfile.TemporaryDirectory()
        self.original_cache = cache.ModalCache
        cache.ModalCache = cache.HashCache(Path(self.temp_cache_dir.name))

    def tearDown(self) -> None:
        cache.ModalCache = self.original_cache
        self.temp_cache_dir.cleanup()

    def test_remember_stores_hash(self):
        """Test that remember() correctly stores a hash in cache."""
        test_hash = "abc123def456"
        cache.remember(test_hash)

        self.assertTrue(test_hash in cache.ModalCache, "Hash should be stored in cache")

    def test_seen_before_returns_true_for_cached_hash(self):
        """Test that seen_before() returns True for a cached hash."""
        test_hash = "cached_hash_123"
        cache.remember(test_hash)

        result = cache.seen_before(test_hash)
        self.assertTrue(result, "seen_before should return True for a cached hash")

    def test_seen_before_returns_false_for_new_hash(self):
        """Test that seen_before() returns False for a new hash."""
        test_hash = "new_hash_456"

        result = cache.seen_before(test_hash)
        self.assertFalse(result, "seen_before should return False for a new hash")

    def test_check_and_remember_first_call(self):
        """Test check_and_remember() on first call (cache miss)."""
        test_hash = "first_time_hash"

        result = cache.check_and_remember(test_hash)

        self.assertFalse(
            result, "check_and_remember should return False on first call (cache miss)"
        )
        self.assertTrue(
            test_hash in cache.ModalCache,
            "Hash should be stored in cache after first call",
        )

    def test_check_and_remember_second_call(self):
        """Test check_and_remember() on second call (cache hit)."""
        test_hash = "second_time_hash"

        # First call - cache miss
        first_result = cache.check_and_remember(test_hash)
        self.assertFalse(first_result, "First call should return False (cache miss)")

        # Second call - cache hit
        second_result = cache.check_and_remember(test_hash)
        self.assertTrue(second_result, "Second call should return True (cache hit)")

    def test_should_notify_modal_first_time(self):
        result = cache.should_notify_modal("Message258")

        self.assertTrue(
            result, "should_notify_modal should return True for a new modal"
        )

    def test_should_notify_modal_second_time(self):
        first_result = cache.should_notify_modal("Message258")
        self.assertTrue(first_result, "First call should return True (new modal)")

        second_result = cache.should_notify_modal("Message258")
        self.assertFalse(
            second_result, "Second call should return False (already seen)"
        )

    def test_should_notify_modal_treats_other_messages_as_new(self):
        cache.should_notify_modal("Message258")

        result = cache.should_notify_modal("Message259")

        self.assertTrue(result, "A different message id should be detected as new")

    def test_should_notify_modal_survives_new_cache_instance(self):
        cache.should_notify_modal("Message258")
        cache.ModalCache = cache.HashCache(Path(self.temp_cache_dir.name))

        result = cache.should_notify_modal("Message258")

        self.assertFalse(result, "Seen message ids should be read back from disk")

    def test_should_notify_modal_ttl(self):
        cache.should_notify_modal("Message258", ttl_seconds=1)

        result_before_expiry = cache.should_notify_modal("Message258", ttl_seconds=1)
        self.assertFalse(result_before_expiry, "Should return False before TTL expiry")

        time.sleep(2)

        result_after_expiry = cache.should_notify_modal("Message258", ttl_seconds=1)
        self.assertTrue(result_after_expiry, "Should return True after TTL expiry")

    @mock.patch("src.cache.check_and_remember")
    def test_should_notify_modal_error_handling(self, check_and_remember_mock):
        check_and_remember_mock.side_effect = Exception("Test error")

        result = cache.should_notify_modal("Message258")
        self.assertTrue(
            result,
            "should_notify_modal should return True on error (notify to be safe)",
        )

    def test_remember_with_custom_ttl(self):
        """Test that remember() respects custom TTL."""
        test_hash = "custom_ttl_hash"

        # Remember with 1 second TTL
        cache.remember(test_hash, ttl_seconds=1)

        # Should exist immediately
        self.assertTrue(
            cache.seen_before(test_hash),
            "Hash should exist immediately after remember()",
        )

        # Wait for expiry
        time.sleep(2)

        # Should be expired
        self.assertFalse(
            cache.seen_before(test_hash), "Hash should be expired after TTL"
        )

    @mock.patch("src.cache.ModalCache.set")
    def test_remember_error_handling(self, mock_set):
        """Test that remember() handles cache.set() errors gracefully."""
        # Make cache.set raise an exception
        mock_set.side_effect = Exception("Cache write error")

        # Should not raise, just log the error
        try:
            cache.remember("error_hash")
        except Exception as e:
            self.fail(f"remember() should handle errors gracefully, but raised: {e}")
