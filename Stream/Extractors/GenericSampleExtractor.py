# This tool was written by @keyiflerolsun | for @KekikAkademi

from KekikStream.Core import ExtractorBase, ExtractResult
from typing           import Optional
import re

class GenericSampleExtractor(ExtractorBase):
    """
    Standardized Video Resolver Template.
    Use this class to implement logic for bypassing video hosting protectors
    and retrieving the final streamable media URL (M3U8/MP4).
    """
    name     = "GenericResolver"
    main_url = "https://example-hosting.com"

    async def extract(self, url: str, referer: Optional[str] = None) -> ExtractResult:
        """
        The extraction logic orchestrates the handshake with the video host.
        """
        # 1. Initialize session with the specified host
        # Base headers and cookies from CloudScraper are pre-loaded in self.httpx
        response = await self.httpx.get(
            url     = url, 
            headers = {"Referer": referer or self.main_url}
        )
        html = response.text

        # 2. Pattern Matching for Stream manifests
        # Generic regex to capture common manifest patterns (m3u8, mp4, etc.)
        stream_pattern = r'["\'](https?://[^"\']+\.(?:m3u8|mp4|webm|mkv)(?:\?[^"\']+)?)["\']'
        match          = re.search(stream_pattern, html)
        
        if not match:
            # Handle obfuscated or protected links (e.g., Base64, AES, Packer)
            raise ValueError(f"Stream resolution failed for source: {url}")

        final_stream_url = match.group(1)

        # 3. Construct Unified Result
        # This object is propagated through the 3-Tier Proxy system in WatchBuddy
        return ExtractResult(
            url        = final_stream_url,
            name       = self.name,
            referer    = url, # Crucial for bypassing segment-level security
            user_agent = self.httpx.headers.get("User-Agent"),
            subtitles  = []   # Add logic to parse <track> or JSON subtitles here
        )
