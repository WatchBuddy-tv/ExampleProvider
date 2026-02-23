# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from fastapi                 import FastAPI, APIRouter, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles     import StaticFiles
from fastapi.responses       import JSONResponse, HTMLResponse, RedirectResponse, PlainTextResponse, FileResponse, StreamingResponse
from .Settings               import PROJECT, HOST, PORT, PROVIDER_NAME, PROVIDER_DESCRIPTION, PROXY_URL, PROXY_FALLBACK_URL, PROXIES

app = FastAPI(title=PROJECT)

# ! ----------------------------------------» Middlewares

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ! ----------------------------------------» Routers

from .Routers.Home.Routers   import home_router
from .Routers.API.v1.Routers import api_v1_router
from .Routers.Proxy.Routers  import proxy_router

app.include_router(home_router)
app.include_router(api_v1_router)
app.include_router(proxy_router)
