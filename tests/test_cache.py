import tempfile
from pathlib import Path
from unittest import TestCase, mock
import time

from PIL import Image
from diskcache import Cache

from src import cache


TEST_PATH = Path(__file__).parent


class TestCache(TestCase):
    """Test suite for the cache module."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Use a temporary cache directory for testing
        self.temp_cache_dir = tempfile.mkdtemp()
        self.original_cache = cache.ModalCache
        cache.ModalCache = Cache(self.temp_cache_dir)

        # Create test images
        self.test_image_path = TEST_PATH / "test_modal_1.png"
        self.test_image_similar_path = TEST_PATH / "test_modal_similar.png"
        self.test_image_different_path = TEST_PATH / "test_modal_different.png"

        # Create test image with horizontal stripes
        img = Image.new("RGB", (100, 100), color="white")
        pixels = img.load()
        for x in range(100):
            for y in range(100):
                if y % 20 < 10:  # Horizontal stripes
                    pixels[x, y] = (255, 0, 0)
        img.save(self.test_image_path)

        # Create similar test image (slightly offset horizontal stripes)
        img_similar = Image.new("RGB", (100, 100), color="white")
        pixels = img_similar.load()
        for x in range(100):
            for y in range(100):
                if y % 20 < 11:  # Slightly thicker stripes
                    pixels[x, y] = (255, 0, 0)
        img_similar.save(self.test_image_similar_path)

        # Create different test image (vertical stripes - very different pattern)
        img_different = Image.new("RGB", (100, 100), color="white")
        pixels = img_different.load()
        for x in range(100):
            for y in range(100):
                if x % 20 < 10:  # Vertical stripes instead
                    pixels[x, y] = (0, 0, 255)
        img_different.save(self.test_image_different_path)

    def tearDown(self) -> None:
        """Clean up test fixtures after each test method."""
        # Restore original cache
        cache.ModalCache = self.original_cache

        # Remove test images
        if self.test_image_path.exists():
            self.test_image_path.unlink()
        if self.test_image_similar_path.exists():
            self.test_image_similar_path.unlink()
        if self.test_image_different_path.exists():
            self.test_image_different_path.unlink()

    def test_perceptual_hash_consistency(self):
        """Test that perceptual_hash returns consistent results for the same image."""
        hash1 = cache.perceptual_hash(self.test_image_path)
        hash2 = cache.perceptual_hash(self.test_image_path)

        self.assertEqual(
            hash1, hash2, "Perceptual hash should be consistent for the same image"
        )
        self.assertIsInstance(hash1, str, "Perceptual hash should return a string")

    def test_perceptual_hash_similar_images(self):
        """Test that similar images produce the same perceptual hash."""
        hash1 = cache.perceptual_hash(self.test_image_path)
        hash_similar = cache.perceptual_hash(self.test_image_similar_path)

        # Similar images should have the same perceptual hash
        self.assertEqual(
            hash1, hash_similar, "Similar images should have the same perceptual hash"
        )

    def test_perceptual_hash_different_images(self):
        """Test that different images produce different perceptual hashes."""
        hash1 = cache.perceptual_hash(self.test_image_path)
        hash_different = cache.perceptual_hash(self.test_image_different_path)

        # Different images should have different perceptual hashes
        self.assertNotEqual(
            hash1,
            hash_different,
            "Different images should have different perceptual hashes",
        )

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
        """Test should_notify_modal() returns True for a new modal."""
        result = cache.should_notify_modal(self.test_image_path)

        self.assertTrue(
            result, "should_notify_modal should return True for a new modal"
        )

    def test_should_notify_modal_second_time(self):
        """Test should_notify_modal() returns False for a seen modal."""
        # First call - should notify
        first_result = cache.should_notify_modal(self.test_image_path)
        self.assertTrue(first_result, "First call should return True (new modal)")

        # Second call - should NOT notify
        second_result = cache.should_notify_modal(self.test_image_path)
        self.assertFalse(
            second_result, "Second call should return False (already seen)"
        )

    def test_should_notify_modal_detects_similar_images(self):
        """Test that should_notify_modal() detects similar images as already seen."""
        # First call with original image
        cache.should_notify_modal(self.test_image_path)

        # Second call with similar image should return False (already seen)
        result = cache.should_notify_modal(self.test_image_similar_path)
        self.assertFalse(result, "Similar modal should be detected as already seen")

    def test_should_notify_modal_different_images(self):
        """Test that should_notify_modal() treats different images as new."""
        # First call with original image
        cache.should_notify_modal(self.test_image_path)

        # Call with different image should return True (new modal)
        result = cache.should_notify_modal(self.test_image_different_path)
        self.assertTrue(result, "Different modal should be detected as new")

    def test_should_notify_modal_ttl(self):
        """Test that should_notify_modal() respects TTL."""
        # Set a very short TTL (1 second)
        cache.should_notify_modal(self.test_image_path, ttl_seconds=1)

        # Immediately should return False (already seen)
        result_before_expiry = cache.should_notify_modal(
            self.test_image_path, ttl_seconds=1
        )
        self.assertFalse(result_before_expiry, "Should return False before TTL expiry")

        # Wait for TTL to expire
        time.sleep(2)

        # After expiry should return True (cache expired, treated as new)
        result_after_expiry = cache.should_notify_modal(
            self.test_image_path, ttl_seconds=1
        )
        self.assertTrue(result_after_expiry, "Should return True after TTL expiry")

    @mock.patch("src.cache.perceptual_hash")
    def test_should_notify_modal_error_handling(self, mock_perceptual_hash):
        """Test that should_notify_modal() handles errors gracefully."""
        # Make perceptual_hash raise an exception
        mock_perceptual_hash.side_effect = Exception("Test error")

        # Should return True (notify) on error to be safe
        result = cache.should_notify_modal(self.test_image_path)
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
