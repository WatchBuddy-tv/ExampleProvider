# This tool was written by @keyiflerolsun | for @KekikAkademi

from FastAPI import JSONResponse
from .       import api_v1_router, api_v1_global_message

from ..Libs.ytdlp_service import ytdlp_extract_video_info

@api_v1_router.get("/ytdlp-extract")
async def ytdlp_extract(url: str = None, user_agent: str = None, referer: str = None):
    if not url:
        return JSONResponse(status_code=400, content={"error": "url parameter required"})

    # Extract video info with yt-dlp
    info = await ytdlp_extract_video_info(url, user_agent=user_agent, referer=referer)

    if not info or not info.get("stream_url"):
        # If yt-dlp fails, use original URL
        return {
            **api_v1_global_message,
            "result" : {
                "title"      : "Video",
                "stream_url" : url,
            "duration"   : 0,
            "is_live"    : False,
            "format"     : "hls" if ".m3u8" in url.lower() else "mp4",
            "user_agent" : "",
            "referer"    : "",
            "resolved"   : False,
            "resolved_by": "fallback"
        }
    }

    # Extract user_agent and referer from HTTP headers
    headers = info.get("http_headers", {})

    return {
        **api_v1_global_message,
        "result" : {
            "title"      : info.get("title", "Video"),
            "stream_url" : info.get("stream_url"),
            "duration"   : info.get("duration", 0),
            "is_live"    : info.get("is_live", False),
            "thumbnail"  : info.get("thumbnail"),
            "format"     : info.get("format", "mp4"),
            "user_agent" : headers.get("user-agent", ""),
            "referer"    : headers.get("referer", ""),
            "resolved"   : True,
            "resolved_by": "ytdlp"
        }
    }
