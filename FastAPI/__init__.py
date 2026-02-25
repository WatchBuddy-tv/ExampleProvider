# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from fastapi                 import FastAPI, APIRouter, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles     import StaticFiles
from fastapi.responses       import JSONResponse, HTMLResponse, RedirectResponse, PlainTextResponse, FileResponse, StreamingResponse
from .Settings               import PROJECT, HOST, PORT, PROVIDER_NAME, PROVIDER_DESCRIPTION, PROXY_URL, PROXY_FALLBACK_URL, PROXIES
from contextlib              import asynccontextmanager
from Kekik.cli               import konsol
from contextlib              import suppress
import asyncio

_availability_checked = False
_availability_lock    = asyncio.Lock()

async def _check_plugin(name: str, plugin, sem: asyncio.Semaphore) -> tuple[str, bool, int | None]:
    if not getattr(plugin, "main_url", None):
        return name, False, None

    async with sem:
        try:
            istek = await plugin.httpx.get(plugin.main_url)
            return name, istek.status_code == 200, istek.status_code
        except Exception:
            return name, False, None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _availability_checked

    async with _availability_lock:
        if not _availability_checked:
            try:
                from Stream import plugin_manager

                plugin_items = list(plugin_manager.plugins.items())
                sem          = asyncio.Semaphore(10)
                checks       = [_check_plugin(name, plugin, sem) for name, plugin in plugin_items]
                results      = await asyncio.gather(*checks)

                removed_count = 0
                for name, is_available, status_code in results:
                    if is_available:
                        continue

                    plugin = plugin_manager.plugins.pop(name, None)
                    if plugin:
                        with suppress(Exception):
                            await plugin.close()
                        removed_count += 1
                        konsol.log(f"[red][!] Plugin unavailable ({status_code or 'ERR'}) : {plugin.name} | {plugin.main_url}")

                _availability_checked = True
                if plugin_items:
                    konsol.log(
                        f"[green]Plugin availability checks completed. "
                        f"({len(plugin_manager.plugins)}/{len(plugin_items)} active, {removed_count} removed, max 10 concurrent)"
                    )
            except Exception as error:
                konsol.log(f"[yellow][!] Plugin availability check skipped: {error}")

    yield

app = FastAPI(title=PROJECT, lifespan=lifespan)

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
