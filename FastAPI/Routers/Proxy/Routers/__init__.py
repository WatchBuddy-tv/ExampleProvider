# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from FastAPI import APIRouter, Request

proxy_router         = APIRouter(prefix="/proxy")
proxy_global_message = {
    "with" : "https://github.com/keyiflerolsun/KekikStream"
}

@proxy_router.get("")
async def get_proxy_router(request: Request):
    return proxy_global_message

from . import video, subtitle
