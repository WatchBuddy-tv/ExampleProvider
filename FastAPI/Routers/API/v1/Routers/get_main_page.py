# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from FastAPI            import Request, JSONResponse
from .                  import api_v1_router, api_v1_global_message
from ..Libs             import plugin_manager
from ..Libs.cache_utils import TTLCache, InflightDedup

from random       import choice
from urllib.parse import quote_plus
import asyncio

_cache = TTLCache(ttl=1800)  # 30 dk - kategori/liste sayfaları sık değişmiyor
_dedup = InflightDedup()

@api_v1_router.get("/get_main_page")
async def get_main_page(request: Request, plugin: str = None, page: int = 1, encoded_url: str = None, encoded_category: str = None):
    plugin_names = plugin_manager.get_plugin_names()
    if not plugin or not encoded_url or not encoded_category:
        return JSONResponse(status_code=410, content={"error": f"{request.url.path}?plugin={choice(plugin_names)}&page=1&encoded_url=&encoded_category="})

    _plugin = plugin if plugin in plugin_names else None
    if not _plugin:
        return JSONResponse(status_code=410, content={"error": f"{request.url.path}?plugin={_plugin or choice(plugin_names)}&page=1&encoded_url=&encoded_category="})

    cache_key = f"{_plugin}|{encoded_url}|{page}|{encoded_category}"
    cached    = _cache.get(cache_key)
    if cached is not None:
        return {**api_v1_global_message, "result": cached}

    async def _load():
        plugin_inst = plugin_manager.select_plugin(_plugin)
        try:
            result = await asyncio.wait_for(plugin_inst.get_main_page(page, encoded_url, encoded_category), timeout=3.0)
        except asyncio.TimeoutError:
            result = []

        for item in result:
            item.url = quote_plus(item.url)

        if result:
            _cache.set(cache_key, result)

        return result

    result = await _dedup.run(cache_key, _load)
    return {**api_v1_global_message, "result": result}
