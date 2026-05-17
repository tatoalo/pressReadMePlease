"""
Caching mechanism to keep track of already notified modals.
This is a disk-based cache, we do have TTL as well.
"""

import json
from pathlib import Path
from time import time

import imagehash
from PIL import Image

from src import CACHE_DIR, logging


CACHE_TTL_SECONDS = 2628000  # 30 days


class HashCache:
    def __init__(self, cache_dir: Path):
        self.cache_file = Path(cache_dir) / "modal_hashes.json"

    def set(self, key: str, value: int, expire: int) -> None:
        del value
        records = self._load()
        records[key] = time() + expire
        self._write(records)

    def __contains__(self, key: str) -> bool:
        records = self._load()
        expires_at = records.get(key)
        if expires_at is None:
            return False
        if expires_at <= time():
            records.pop(key, None)
            self._write(records)
            return False
        return True

    def _load(self) -> dict[str, float]:
        if not self.cache_file.exists():
            return {}
        try:
            raw_records = json.loads(self.cache_file.read_text())
        except (json.JSONDecodeError, OSError) as e:
            logging.error(f"Failed to read modal hash cache: {e}")
            return {}
        return {
            str(key): float(value)
            for key, value in raw_records.items()
            if isinstance(value, int | float)
        }

    def _write(self, records: dict[str, float]) -> None:
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(records, sort_keys=True))


ModalCache = HashCache(CACHE_DIR)


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
