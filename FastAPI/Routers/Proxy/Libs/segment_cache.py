# This tool was written by @keyiflerolsun | for @KekikAkademi

from time import time
import asyncio

class SegmentCache:
    """
    LRU cache - HLS video segmentleri için
    - 128MB boyut limiti
    - En az kullanılan (LRU) segment'ler silinir
    - 15 dakika hard TTL (stream token güvenliği için)
    """

    def __init__(self, max_size_mb: int = 128, hard_ttl_seconds: int = 900):  # 900s = 15 minutes
        self.max_size_bytes   = max_size_mb * 1024 * 1024
        self.hard_ttl_seconds = hard_ttl_seconds

        # Cache storage: {url: (content, created_at, last_access, size)}
        self._cache: dict[str, tuple[bytes, float, float, int]] = {}
        self._total_size = 0
        self._lock = asyncio.Lock()

    async def get(self, url: str) -> bytes | None:
        """Get segment from cache and update access time"""
        async with self._lock:
            if url not in self._cache:
                return None

            content, created_at, _, size = self._cache[url]

            # Hard TTL check (15 minutes)
            if time() - created_at > self.hard_ttl_seconds:
                # Expired, delete
                del self._cache[url]
                self._total_size -= size
                return None

            # Update last access time (for LRU)
            self._cache[url] = (content, created_at, time(), size)

            return content

    async def set(self, url: str, content: bytes):
        """Add segment to cache"""
        async with self._lock:
            content_size = len(content)

            # Max size check - do not cache if new content is too large
            if content_size > self.max_size_bytes:
                return

            # If this URL is already in cache, subtract old size first
            if url in self._cache:
                _, _, _, old_size = self._cache[url]
                self._total_size -= old_size

            # Add new content (content, created_at, last_access, size)
            current_time = time()
            self._cache[url] = (content, current_time, current_time, content_size)
            self._total_size += content_size

            # LRU eviction - delete least used if size limit exceeded
            await self._evict_if_needed()

    async def _evict_if_needed(self):
        """Delete least used items if necessary"""
        current_time = time()

        # Clean up items with expired Hard TTL (15 minutes)
        expired_urls = [
            url for url, (_, created_at, _, _) in self._cache.items()
            if current_time - created_at > self.hard_ttl_seconds
        ]
        for url in expired_urls:
            _, _, _, size = self._cache[url]
            del self._cache[url]
            self._total_size -= size

        # If 128MB limit is still exceeded, delete least used (LRU) items
        while self._total_size > self.max_size_bytes:
            if not self._cache:
                break

            # Find least used item (smallest last_access)
            lru_url = min(self._cache.items(), key=lambda x: x[1][2])[0]  # [1][2] = last_access
            _, _, _, size = self._cache[lru_url]
            del self._cache[lru_url]
            self._total_size -= size

    def get_stats(self) -> dict:
        """Cache statistics"""
        return {
            "total_items"      : len(self._cache),
            "total_size_mb"    : round(self._total_size / (1024 * 1024), 2),
            "max_size_mb"      : round(self.max_size_bytes / (1024 * 1024), 2),
            "hard_ttl_minutes" : self.hard_ttl_seconds // 60,
        }

# Global cache instance
segment_cache = SegmentCache(max_size_mb=128, hard_ttl_seconds=900)