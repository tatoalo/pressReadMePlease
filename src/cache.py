"""
Caching mechanism to keep track of already notified modals.
This is a disk-based cache, we do have TTL as well.
"""

import json
from pathlib import Path
from time import time

from src import CACHE_DIR, logging


CACHE_TTL_SECONDS = 2628000  # 30 days


class HashCache:
    def __init__(self, cache_dir: Path):
        self.cache_file = Path(cache_dir) / "modal_hashes.json"

    def set(self, key: str, expire: int) -> None:
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
            logging.error(f"Failed to read modal cache: {e}")
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


def remember(key: str, ttl_seconds: int = CACHE_TTL_SECONDS) -> None:
    try:
        ModalCache.set(key, expire=ttl_seconds)
        logging.debug(f"Remembered modal {key} with TTL {ttl_seconds}s")
    except Exception as e:
        logging.error(f"Failed to cache modal {key}: {e}")


def seen_before(key: str) -> bool:
    return key in ModalCache


def check_and_remember(key: str, ttl_seconds: int = CACHE_TTL_SECONDS) -> bool:
    if seen_before(key):
        logging.debug(f"Modal {key} already seen (hit)")
        return True

    logging.debug(f"Modal {key} is NEW (miss)")
    remember(key, ttl_seconds)
    return False


def should_notify_modal(key: str, ttl_seconds: int = CACHE_TTL_SECONDS) -> bool:
    try:
        return not check_and_remember(key, ttl_seconds)
    except Exception as e:
        logging.error(f"Error checking modal {key}: {e}")
        return True
