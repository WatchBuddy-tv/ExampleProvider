# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from FastAPI import Request, JSONResponse
from .       import api_v1_router, api_v1_global_message
from ..Libs  import plugin_manager
from random  import choice

@api_v1_router.get("/load_links")
async def load_links(request: Request, plugin: str = None, encoded_url: str = None):
    plugin_names = plugin_manager.get_plugin_names()
    if not plugin or not encoded_url:
        return JSONResponse(status_code=410, content={"hata": f"{request.url.path}?plugin={choice(plugin_names)}&encoded_url="})

    _plugin = plugin if plugin in plugin_names else None
    if not _plugin:
        return JSONResponse(status_code=410, content={"hata": f"{request.url.path}?plugin={_plugin or choice(plugin_names)}&encoded_url="})

    plugin = plugin_manager.select_plugin(_plugin)
    links  = await plugin.load_links(encoded_url)

    result = []
    for link in links:
        subtitles = []
        if link.subtitles:
            subtitles = [sub.model_dump() for sub in link.subtitles]

        result.append({
            "name"       : link.name,
            "url"        : link.url,
            "referer"    : link.referer or "",
            "user_agent" : link.user_agent or "",
            "subtitles"  : subtitles
        })

    return {**api_v1_global_message, "result": result}
