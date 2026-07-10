# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from FastAPI      import Request, JSONResponse
from .            import api_v1_router, api_v1_global_message
from ..Libs       import extractor_manager
from urllib.parse import urlparse
import asyncio, time

# Global safety guards
_extraction_semaphores = {}  # domain -> Semaphore(5) - hoster başına, siteler birbirini bloklamasın
_extraction_sem_lock   = asyncio.Lock()
_inflight_extractions  = {}  # URL -> Future
_negative_cache        = {}  # URL -> (timestamp, error_msg)
_NEG_CACHE_TTL         = 300  # 5 minutes
_NEG_CACHE_MAX_ENTRIES = 5000

async def _get_domain_semaphore(url: str) -> asyncio.Semaphore:
    domain = urlparse(url).netloc
    async with _extraction_sem_lock:
        if domain not in _extraction_semaphores:
            _extraction_semaphores[domain] = asyncio.Semaphore(5)
        return _extraction_semaphores[domain]

def _prune_bounded_cache(cache: dict, max_entries: int = 5000):
    """Basit boyut sınırı: limit aşılırsa en eski kayıtları sil (FIFO, insertion-order dict)."""
    overflow = len(cache) - max_entries
    if overflow > 0:
        for key in list(cache.keys())[:overflow]:
            cache.pop(key, None)

@api_v1_router.get("/extract")
async def extract(request: Request, encoded_url: str = None, encoded_referer: str = None):
    if not encoded_url:
        return JSONResponse(status_code=410, content={"error": f"{request.url.path}?_encoded_url=&_encoded_referer="})

    # Doğrudan medya dosyaları için bypass (m3u8, mp4 vb.)
    url_lower = encoded_url.lower()
    is_direct = any(ext in url_lower for ext in (".m3u8", ".mp4", ".mpd", ".webm", ".mkv", ".avi", ".mov", ".flv", ".wmv"))
    if is_direct:
        return {
            **api_v1_global_message,
            "result"        : {
                "name"          : "direct",
                "url"           : encoded_url,
                "referer"       : encoded_referer,
                "user_agent"    : request.headers.get("user-agent"),
                "extra_headers" : {},
                "subtitles"     : []
            }
        }

    # --- Safety 1: Negative Cache (Cache Miss Protection) ---
    now = time.time()
    if encoded_url in _negative_cache:
        ts, err = _negative_cache[encoded_url]
        if (now - ts) < _NEG_CACHE_TTL:
            return JSONResponse(status_code=503, content={"error": f"URL is temporarily blocked: {err}"})
        else:
            _negative_cache.pop(encoded_url)

    # --- Safety 2: Async Singleton Task (Deduplication) ---
    if encoded_url in _inflight_extractions:
        return await _inflight_extractions[encoded_url]

    async def _do_extract():
        extractor = extractor_manager.find_extractor(encoded_url)
        if not extractor:
            _negative_cache[encoded_url] = (time.time(), "Extractor not found")
            _prune_bounded_cache(_negative_cache, _NEG_CACHE_MAX_ENTRIES)
            return JSONResponse(status_code=404, content={"error": "Extractor not found."})

        sem = await _get_domain_semaphore(encoded_url)
        async with sem:
            try:
                # Add a reasonable timeout for the whole operation
                result = await asyncio.wait_for(
                    extractor.extract(encoded_url, encoded_referer),
                    timeout=15.0
                )
                return {**api_v1_global_message, "result": result}
            except asyncio.TimeoutError:
                _negative_cache[encoded_url] = (time.time(), "Timeout")
                _prune_bounded_cache(_negative_cache, _NEG_CACHE_MAX_ENTRIES)
                return JSONResponse(status_code=504, content={"error": "Extraction timed out."})
            except Exception as e:
                _negative_cache[encoded_url] = (time.time(), str(e))
                _prune_bounded_cache(_negative_cache, _NEG_CACHE_MAX_ENTRIES)
                return JSONResponse(status_code=500, content={"error": str(e)})

    # Create task and track it
    task = asyncio.create_task(_do_extract())
    _inflight_extractions[encoded_url] = task

    try:
        return await task
    finally:
        _inflight_extractions.pop(encoded_url, None)
