# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from .cache_utils import TTLCache
from Stream       import extractor_manager
import asyncio, subprocess, json, os

# Singleton YTDLP extractor instance
_ytdlp_extractor = None
for extractor_cls in extractor_manager.extractors:
    instance = extractor_cls()
    if instance.name == "yt-dlp":
        _ytdlp_extractor = instance
        break

_CACHE_TTL = int(os.getenv("YTDLP_CACHE_TTL", "600") or "600")
_NEG_TTL   = int(os.getenv("YTDLP_NEG_TTL", "60") or "60")

_cache     = TTLCache(ttl=_CACHE_TTL, max_entries=256)
_neg_cache = TTLCache(ttl=_NEG_TTL, max_entries=256)
_lock      = asyncio.Lock()

async def ytdlp_extract_video_info(url: str, user_agent: str | None = None, referer: str | None = None):
    """
    Extract video info with yt-dlp

    Uses YTDLP extractor's fast-path regex check to
    validate URL first, then extract info.

    Args:
        url: Video URL

    Returns:
        {
            "title"      : str,
            "stream_url" : str,
            "duration"   : float,
            "thumbnail"  : str,
            "format"     : str  # "hls" | "mp4" | "webm"
        }
    """
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        return None

    if not _ytdlp_extractor or not _ytdlp_extractor.can_handle_url(url):
        return None

    cache_key = f"{url}|{user_agent or ''}|{referer or ''}"
    async with _lock:
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached
        if _neg_cache.get(cache_key) is not None:
            return None

    # If URL is valid, extract full info
    info = await _extract_with_ytdlp(url, user_agent=user_agent, referer=referer)
    async with _lock:
        if info:
            _cache.set(cache_key, info)
        else:
            _neg_cache.set(cache_key, True)
    return info

async def _extract_with_ytdlp(url: str, user_agent: str | None = None, referer: str | None = None):
    """Extract video info with yt-dlp (internal)"""
    try:
        cmd = [
            "yt-dlp",
            "--no-warnings",
            "--no-playlist",
            "--socket-timeout", "10",
            "-j",  # JSON output
            "-f", "best/all",
            "--format-sort", "proto:https",  # Prefer HTTPS (progressive) over HLS
            url
        ]
        if user_agent:
            cmd.insert(-1, f"--user-agent={user_agent}")
        if referer:
            cmd.insert(-1, f"--referer={referer}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )

        timeout_s = float(os.getenv("YTDLP_TIMEOUT", "5") or "5")
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout = timeout_s
            )
        except asyncio.TimeoutError:
            # wait_for coroutine'i iptal eder ama subprocess çalışmaya devam eder → zombie process leak
            process.kill()
            await process.wait()
            raise

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            return None

        # JSON parse
        stdout_str = stdout.decode().strip()
        if not stdout_str:
            print(f"yt-dlp returned empty output for URL: {url}")
            return None

        info = json.loads(stdout_str)

        # Determine format
        ext       = info.get("ext", "mp4").lower()
        url_lower = info.get("url", "").lower()

        if "m3u8" in url_lower or info.get("protocol") == "m3u8_native":
            video_format = "hls"
        elif ext in ["mp4", "webm", "mkv", "avi", "mov", "flv", "wmv"]:
            video_format = ext
        else:
            video_format = "mp4"

        return {
            "title"        : info.get("title", "Video"),
            "stream_url"   : info.get("url"),
            "duration"     : info.get("duration", 0),
            "is_live"      : bool(info.get("is_live")) if info.get("is_live") is not None else False,
            "thumbnail"    : info.get("thumbnail"),
            "format"       : video_format,
            "uploader"     : info.get("uploader", ""),
            "description"  : info.get("description", "")[:200] if info.get("description") else "",
            "http_headers" : {k.lower() : v for k, v in info.get("http_headers", {}).items()}
        }

    except asyncio.TimeoutError:
        return None
    except json.JSONDecodeError as e:
        return None
    except FileNotFoundError:
        return None
    except Exception as e:
        return None
