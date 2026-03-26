# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from FastAPI import JSONResponse, RedirectResponse
from .       import home_router

@home_router.get("/")
async def home():
    """Home Page"""
    return RedirectResponse("https://github.com/WatchBuddy-tv/ExampleProvider")

@home_router.get("/health")
@home_router.head("/health")
async def health_check():
    """Health Check"""
    return JSONResponse({"success": True, "status": "healthy"})
