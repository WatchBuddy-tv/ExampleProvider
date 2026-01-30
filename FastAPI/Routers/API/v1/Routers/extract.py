# This tool was written by @keyiflerolsun | for @KekikAkademi

from FastAPI import Request, JSONResponse
from .       import api_v1_router, api_v1_global_message
from ..Libs  import extractor_manager

@api_v1_router.get("/extract")
async def extract(request: Request, encoded_url: str = None, encoded_referer: str = None):
    if not encoded_url:
        return JSONResponse(status_code=410, content={"error": f"{request.url.path}?_encoded_url=&_encoded_referer="})

    extractor = extractor_manager.find_extractor(encoded_url)
    if not extractor:
        return JSONResponse(status_code=404, content={"error": "Extractor not found."})

    result = await extractor.extract(encoded_url, encoded_referer)

    return {**api_v1_global_message, "result": result}
