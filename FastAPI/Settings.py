# This tool was written by @keyiflerolsun | for @KekikAkademi

from pathlib import Path
from yaml    import load, FullLoader
from dotenv  import load_dotenv
import os

# .env loading
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Settings.yml loading
with open("Settings.yml", "r", encoding="utf-8") as yaml_file:
    SETTINGS = load(yaml_file, Loader=FullLoader)

# General settings
PROJECT = SETTINGS["PROJECT"]
HOST    = SETTINGS["APP"]["HOST"]
PORT    = SETTINGS["APP"]["PORT"]

# Provider Metadata
def _clean_url(value: str) -> str:
    cleaned = (value or "").strip()
    return cleaned.rstrip("/") if cleaned else ""

PROVIDER_NAME        = os.getenv("PROVIDER_NAME", PROJECT)
PROVIDER_DESCRIPTION = os.getenv("PROVIDER_DESCRIPTION", "KekikStream Content Provider")
PROXY_URL            = _clean_url(os.getenv("PROXY_URL", ""))
PROXY_FALLBACK_URL   = _clean_url(os.getenv("PROXY_FALLBACK_URL", ""))

# Proxy settings (Outgoing)
http_proxy  = os.getenv("HTTP_PROXY", None)
https_proxy = os.getenv("HTTPS_PROXY", None)

if http_proxy and https_proxy:
    PROXIES = {
        "http"  : http_proxy,
        "https" : https_proxy,
    }
else:
    PROXIES = None
