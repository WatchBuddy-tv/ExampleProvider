# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from FastAPI import Request, JSONResponse
from .       import api_v1_router, api_v1_global_message

from ..Libs.ytdlp_service import ytdlp_extract_video_info

@api_v1_router.get("/ytdlp-extract")
async def ytdlp_extract(url: str = None):
    if not url:
        return JSONResponse(status_code=400, content={"hata": "url parametresi gerekli"})

    # yt-dlp ile video bilgisi çıkar
    info = await ytdlp_extract_video_info(url)

    if not info or not info.get("stream_url"):
        # yt-dlp bulamadıysa, orijinal URL'i kullan
        return {
            **api_v1_global_message,
            "result" : {
                "title"      : "Video",
                "stream_url" : url,
                "duration"   : 0,
                "format"     : "hls" if ".m3u8" in url.lower() else "mp4",
                "user_agent" : "",
                "referer"    : ""
            }
        }

    # HTTP headers'dan user_agent ve referer çıkar
    headers = info.get("http_headers", {})

    return {
        **api_v1_global_message,
        "result" : {
            "title"      : info.get("title", "Video"),
            "stream_url" : info.get("stream_url"),
            "duration"   : info.get("duration", 0),
            "thumbnail"  : info.get("thumbnail"),
            "format"     : info.get("format", "mp4"),
            "user_agent" : headers.get("user-agent", ""),
            "referer"    : headers.get("referer", "")
        }
    }
