# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from FastAPI import Request, JSONResponse
from .       import api_v1_router, api_v1_global_message
from ..Libs  import plugin_manager, SeriesInfo

from random       import choice
from urllib.parse import quote_plus
import asyncio, time

# Global safety guards
_load_item_semaphore = asyncio.Semaphore(10)
_inflight_loads      = {}  # CacheKey -> Future
_negative_cache      = {}  # CacheKey -> (timestamp, error_msg)
_NEG_CACHE_TTL       = 300  # 5 minutes

@api_v1_router.get("/load_item")
async def load_item(request: Request, plugin: str = None, encoded_url: str = None):
    plugin_names = plugin_manager.get_plugin_names()
    if not plugin or not encoded_url:
        return JSONResponse(status_code=410, content={"error": f"{request.url.path}?plugin={choice(plugin_names)}&encoded_url="})

    _plugin = plugin if plugin in plugin_names else None
    if not _plugin:
        return JSONResponse(status_code=410, content={"error": f"{request.url.path}?plugin={_plugin or choice(plugin_names)}&encoded_url="})

    # --- Safety 1: Negative Cache (Cache Miss Protection) ---
    cache_key = f"{_plugin}|{encoded_url}"
    now       = time.time()
    if cache_key in _negative_cache:
        ts, err = _negative_cache[cache_key]
        if (now - ts) < _NEG_CACHE_TTL:
            return JSONResponse(status_code=503, content={"error": f"Item is temporarily blocked: {err}"})
        else:
            _negative_cache.pop(cache_key)

    # --- Safety 2: Async Singleton Task (Deduplication) ---
    if cache_key in _inflight_loads:
        return await _inflight_loads[cache_key]

    async def _do_load():
        async with _load_item_semaphore:
            try:
                plugin_inst = plugin_manager.select_plugin(_plugin)
                result      = await asyncio.wait_for(
                    plugin_inst.load_item(encoded_url),
                    timeout=3.0
                )

                if not result:
                    _negative_cache[cache_key] = (time.time(), "Item not found")
                    return JSONResponse(status_code=404, content={"error": "Item not found."})

                result.url = quote_plus(result.url)

                if isinstance(result, SeriesInfo):
                    for episode in result.episodes:
                        episode.url = quote_plus(episode.url)

                return {**api_v1_global_message, "result": result}
            except asyncio.TimeoutError:
                _negative_cache[cache_key] = (time.time(), "Timeout")
                return JSONResponse(status_code=504, content={"error": "Item load timed out."})
            except Exception as e:
                _negative_cache[cache_key] = (time.time(), str(e))
                return JSONResponse(status_code=500, content={"error": str(e)})

    # Create task and track it
    task = asyncio.create_task(_do_load())
    _inflight_loads[cache_key] = task

    try:
        return await task
    finally:
        _inflight_loads.pop(cache_key, None)
