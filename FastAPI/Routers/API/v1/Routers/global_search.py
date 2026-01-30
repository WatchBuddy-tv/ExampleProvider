# This tool was written by @keyiflerolsun | for @KekikAkademi

from FastAPI import Request, JSONResponse
from .       import api_v1_router, api_v1_global_message
from ..Libs  import plugin_manager

import asyncio
from urllib.parse import quote_plus

@api_v1_router.get("/global_search")
async def global_search(query: str = None):
    if not query:
        return JSONResponse(status_code=410, content={"error": "Query parameter missing!"})

    plugin_names = plugin_manager.get_plugin_names()

    async def search_in_plugin(name):
        try:
            plugin = plugin_manager.select_plugin(name)
            results = await plugin.search(query)
            for item in results:
                item.url = quote_plus(item.url)
                item.plugin = name # Save plugin name
            return results
        except:
            return []

    # Search all plugins in parallel
    tasks = [search_in_plugin(name) for name in plugin_names]
    all_results_lists = await asyncio.gather(*tasks)

    # Merge lists
    combined_results = []
    for results in all_results_lists:
        combined_results.extend(results)

    return {**api_v1_global_message, "result": combined_results}
