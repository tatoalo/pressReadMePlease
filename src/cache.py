"""
Caching mechanism to keep track of already notified modals.
This is a disk-based cache, we do have TTL as well.
"""

from diskcache import Cache
from src import CACHE_DIR, logging

from pathlib import Path

from PIL import Image
import imagehash


CACHE_TTL_SECONDS = 2628000  # 30 days

ModalCache = Cache(CACHE_DIR)


def remember(h: str, ttl_seconds: int = CACHE_TTL_SECONDS) -> None:
    try:
        ModalCache.set(h, 1, expire=ttl_seconds)
        logging.debug(f"Remembered hash {h[:8]}... with TTL {ttl_seconds}s")
    except Exception as e:
        logging.error(f"Failed to cache hash {h[:8]}...: {e}")


def seen_before(h: str) -> bool:
    return h in ModalCache


def check_and_remember(h: str, ttl_seconds: int = CACHE_TTL_SECONDS) -> bool:
    if seen_before(h):
        logging.debug(f"Modal hash {h[:8]}... already seen (hit)")
        return True

    logging.debug(f"Modal hash {h[:8]}... is NEW (miss)")
    remember(h, ttl_seconds)
    return False


def perceptual_hash(screenshot_path: Path) -> str:
    img = Image.open(screenshot_path)
    return str(imagehash.average_hash(img))


def should_notify_modal(
    screenshot_path: Path, ttl_seconds: int = CACHE_TTL_SECONDS
) -> bool:
    """
    Check if a modal screenshot should trigger a notification.
    Returns True if this is a new modal, False if already seen.
    """
    try:
        screenshot_hash = perceptual_hash(screenshot_path)
        is_seen = check_and_remember(screenshot_hash, ttl_seconds)
        return not is_seen
    except Exception as e:
        logging.error(f"Error checking modal screenshot: {e}")
        # On error, notify just to be safe
        return True
