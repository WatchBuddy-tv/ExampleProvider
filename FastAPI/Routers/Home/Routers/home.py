# This tool was written by @keyiflerolsun | for @KekikAkademi

from FastAPI import JSONResponse
from .       import home_router

@home_router.get("/")
@home_router.get("/health")
@home_router.head("/health")
async def health_check():
    """Health Check"""
    return JSONResponse({"success": True, "status": "healthy"})
