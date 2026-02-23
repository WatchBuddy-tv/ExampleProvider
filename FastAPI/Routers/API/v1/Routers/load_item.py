# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from FastAPI import Request, JSONResponse
from .       import api_v1_router, api_v1_global_message
from ..Libs  import plugin_manager, SeriesInfo

from random       import choice
from urllib.parse import quote_plus

@api_v1_router.get("/load_item")
async def load_item(request: Request, plugin: str = None, encoded_url: str = None):
    plugin_names = plugin_manager.get_plugin_names()
    if not plugin or not encoded_url:
        return JSONResponse(status_code=410, content={"error": f"{request.url.path}?plugin={choice(plugin_names)}&encoded_url="})

    _plugin = plugin if plugin in plugin_names else None
    if not _plugin:
        return JSONResponse(status_code=410, content={"error": f"{request.url.path}?plugin={_plugin or choice(plugin_names)}&encoded_url="})

    plugin = plugin_manager.select_plugin(_plugin)
    result = await plugin.load_item(encoded_url)

    result.url = quote_plus(result.url)

    if isinstance(result, SeriesInfo):
        for episode in result.episodes:
            episode.url = quote_plus(episode.url)

    return {**api_v1_global_message, "result": result}
