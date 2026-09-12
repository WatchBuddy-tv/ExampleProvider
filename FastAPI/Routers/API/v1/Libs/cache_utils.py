# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

import asyncio, time


class TTLCache:
    """Basit süreli önbellek. Aynı sorgu tekrar gelirse siteyi yeniden kazımaz."""

    def __init__(self, ttl: float, max_entries: int = 500):
        self.ttl         = ttl
        self.max_entries = max_entries
        self._store      = {}

    def get(self, key):
        entry = self._store.get(key)
        if not entry:
            return None

        expires_at, value = entry
        if time.time() >= expires_at:
            self._store.pop(key, None)
            return None

        return value

    def set(self, key, value):
        now              = time.time()
        self._store[key] = (now + self.ttl, value)

        # Boyut aşıldıysa önce süresi dolmuşları temizle
        if len(self._store) > self.max_entries:
            expired = [k for k, (exp, _) in self._store.items() if exp <= now]
            for k in expired:
                self._store.pop(k, None)

        # Hala taştıysa en eskileri at (FIFO)
        overflow = len(self._store) - self.max_entries
        if overflow > 0:
            for old_key in list(self._store.keys())[:overflow]:
                self._store.pop(old_key, None)


class InflightDedup:
    """Aynı key için eşzamanlı istekleri tek task'a düşürür (thundering herd önleme)."""

    def __init__(self):
        self._tasks = {}
        self._lock  = asyncio.Lock()

    async def run(self, key, coro_func):
        async with self._lock:
            task = self._tasks.get(key)
            if task is None:
                task = asyncio.create_task(coro_func())
                self._tasks[key] = task

        try:
            return await task
        finally:
            async with self._lock:
                if self._tasks.get(key) is task:
                    self._tasks.pop(key, None)
