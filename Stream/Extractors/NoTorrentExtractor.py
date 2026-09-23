# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from KekikStream.Core import ExtractorBase, ExtractResult

class NoTorrentExtractor(ExtractorBase):
    """
    NoTorrent Redirect Stream Resolver.
    Follows NoTorrent redirect URLs to get the final playable media stream.
    """
    name              = "NoTorrent"
    main_url          = "https://addon.notorrent2.workers.dev"
    supported_domains = ["addon.notorrent2.workers.dev", "hostingersite.com"]

    async def extract(self, url: str, referer: str | None = None) -> ExtractResult:
        """
        Extract the direct video stream URL by following the redirect.
        """
        if "redirect" in url:
            # Follow redirects to get the final stream URL
            response  = await self.httpx.get(url, follow_redirects=True)
            final_url = str(response.url)
        else:
            final_url = url

        return ExtractResult(
            url        = final_url,
            name       = self.name,
            referer    = referer or url,
            user_agent = self.httpx.headers.get("User-Agent"),
            subtitles  = []
        )
