# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from FastAPI import Request, PROVIDER_NAME, PROVIDER_DESCRIPTION, PROXY_URL, PROXY_FALLBACK_URL
from .       import api_v1_router

@api_v1_router.get("/schema")
async def get_schema(request: Request):
    """Provider Schema (Discovery) endpoint"""
    return {
        "provider_name"      : PROVIDER_NAME,
        "description"        : PROVIDER_DESCRIPTION,
        "proxy_url"          : PROXY_URL or str(request.base_url).rstrip("/"),
        "proxy_fallback_url" : PROXY_FALLBACK_URL
    }
