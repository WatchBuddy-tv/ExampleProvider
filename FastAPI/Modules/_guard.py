# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from ..          import app as kekik_FastAPI, Request, Response
from ._IP_Log    import ip_log
from collections import defaultdict, deque
from time        import time
import asyncio, os

# ! ----------------------------------------» Güvenlik Listeleri
_BLOCKED_IPS  = []
_BLOCKED_ISPS = [
    "contabo", "digitalocean", "hetzner", "ovh", "linode", "amazon", "google", "azure",
    "vultr", "choopa", "m247", "alexhost", "datacamp", "zenlayer", "verizon", "carat",
    "unitas", "alastyr", "veridyen", "radore", "dgn", "premierdc", "netasistan", "hosting", "datacenter"
]
_RATE_LIMIT_ENABLED          = (os.getenv("RATE_LIMIT_ENABLED", "true") or "true").strip().lower() in ("1", "true", "yes", "on")
_RATE_LIMIT_MAX_REQUESTS     = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "180") or "180")
_RATE_LIMIT_WINDOW_SECONDS   = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60") or "60")
_RATE_LIMIT_EXEMPT_PATH_PART = (
    "/health",
    "/favicon.ico",
    "/static",
    "/webfonts",
    "/manifest.json",
    "com.chrome.devtools.json",
)

# (IP, endpoint, plugin_adi) -> deque[timestamps]
_rate_limit_hits = defaultdict(deque)
_rate_limit_lock = asyncio.Lock()

# IP API sorgu limitini korumak için Cache mekanizması
_ISP_CACHE = {}

async def _check_ip_rate_limit(client_ip: str, request: Request) -> tuple[bool, int]:
    if not _RATE_LIMIT_ENABLED:
        return True, 0

    request_path = request.url.path
    if any(skip in request_path for skip in _RATE_LIMIT_EXEMPT_PATH_PART):
        return True, 0

    now = time()
    async with _rate_limit_lock:
        rate_key = (client_ip, request_path)
        hits     = _rate_limit_hits[rate_key]
        cutoff   = now - _RATE_LIMIT_WINDOW_SECONDS

        while hits and hits[0] <= cutoff:
            hits.popleft()

        if len(hits) >= _RATE_LIMIT_MAX_REQUESTS:
            retry_after = max(1, int(_RATE_LIMIT_WINDOW_SECONDS - (now - hits[0])))
            return False, retry_after

        hits.append(now)
        return True, 0

@kekik_FastAPI.middleware("http")
async def guvenlik_duvari(request: Request, call_next):
    # ! 1. IP Tespiti (Cloudflare ve Proxy Desteği ile)
    fw_for    = request.headers.get("X-Forwarded-For")
    cf_ip     = request.headers.get("Cf-Connecting-Ip")
    client_ip = cf_ip or (fw_for.split(",")[0].strip() if fw_for else request.client.host)

    # ! 2. Manuel IP Engelleme
    if client_ip in _BLOCKED_IPS:
        return Response(status_code=403, content="IP Blocked")

    # ! 3. Rate Limit Kontrolü
    allowed, retry_after = await _check_ip_rate_limit(client_ip, request)
    if not allowed:
        return Response(
            status_code = 429,
            headers     = {"Retry-After": str(retry_after)},
            content     = "Too Many Requests for this resource"
        )

    # ! 4. ISP / Veri Merkezi Bloklama
    if client_ip in _ISP_CACHE:
        isp_bilgisi = _ISP_CACHE[client_ip]
    else:
        try:
            ip_detay               = await ip_log(client_ip)
            request.state.ip_detay = ip_detay  # _istek.py loglaması için sakla

            # Tüm değerleri birleştirip küçük harfe çevirerek kontrol et
            isp_bilgisi = " ".join(str(v) for v in ip_detay.values()).lower()
            _ISP_CACHE[client_ip] = isp_bilgisi
        except Exception:
            isp_bilgisi = ""

    if any(sirket in isp_bilgisi for sirket in _BLOCKED_ISPS):
        return Response(status_code=403, content="Datacenter/Bot Traffic Blocked")

    return await call_next(request)
