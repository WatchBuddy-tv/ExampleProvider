# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from FastAPI import Request, JSONResponse
from .       import api_v1_router, api_v1_global_message
from ..Libs  import plugin_manager

from random       import choice
from urllib.parse import quote_plus

@api_v1_router.get("/get_plugin")
async def get_plugin(request: Request, plugin: str = None):
    plugin_names = plugin_manager.get_plugin_names()
    if not plugin:
        return JSONResponse(status_code=410, content={"error": f"{request.url.path}?plugin={choice(plugin_names)}"})

    _plugin = plugin if plugin in plugin_names else None
    if not _plugin:
        return JSONResponse(status_code=410, content={"error": f"{request.url.path}?plugin={_plugin or choice(plugin_names)}"})

    plugin = plugin_manager.select_plugin(_plugin)

    main_page = {}
    for url, category in plugin.main_page.items():
        main_page[quote_plus(url)] = quote_plus(category)

    result = {
        "name"        : plugin.name,
        "language"    : plugin.language,
        "main_url"    : plugin.main_url,
        "favicon"     : plugin.favicon,
        "description" : plugin.description,
        "main_page"   : main_page
    }

    return {**api_v1_global_message, "result": result}
