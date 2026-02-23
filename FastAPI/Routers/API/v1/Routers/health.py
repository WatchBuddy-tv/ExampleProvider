# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from FastAPI import JSONResponse
from .       import api_v1_router

@api_v1_router.get("/health")
async def health_check():
    """API Health Check"""
    return JSONResponse({"success": True, "status": "healthy"})
