# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from KekikStream.Core import PluginBase, MainPageResult, SearchResult, Episode, MovieInfo, SeriesInfo, ExtractResult
from urllib.parse     import quote
import re, asyncio

class Stremio(PluginBase):
    """Stremio Wrapper (Discovery: Cinemeta | Streams: Streailer + NoTorrent)"""
    name        = "Stremio"
    language    = "multi"
    main_url    = "https://web.stremio.com"
    favicon     = f"https://www.google.com/s2/favicons?domain={main_url}&sz=64"
    description = "Combined Stremio Wrapper (Cinemeta Catalogs + Streailer/NoTorrent Streams)"

    # API Resources
    CINEMETA  = "https://v3-cinemeta.strem.io"
    STREAILER = "https://9aa032f52161-streailer.baby-beamup.club"
    NOTORRENT = "https://addon.notorrent2.workers.dev"

    # Expanded Main Page categories
    main_page = {
        "movie/top"         : "Popular Movies",
        "series/top"        : "Popular Series",
        "movie/imdbRating"  : "Top Rated Movies",
        "series/imdbRating" : "Top Rated Series",
        "movie/year"        : "New Movies",
        "series/year"       : "New Series",
    }

    async def get_main_page(self, page: int, url: str, category: str) -> list[MainPageResult]:
        """Fetch and parse main page results from Cinemeta catalogs"""
        # skip = (page - 1) * 20
        req   = await self.httpx.get(f"{self.CINEMETA}/catalog/{url}.json?skip={(page - 1) * 20}")
        data  = req.json()
        metas = data.get('metas', [])

        return [
            MainPageResult(
                category = category,
                title    = item['name'],
                url      = f"{item['type']}/{item['id']}",
                poster   = item.get('poster')
            )
                for item in metas
        ]

    async def search(self, query: str) -> list[SearchResult]:
        """Search for content using Cinemeta's search functionality"""
        req   = await self.httpx.get(f"{self.CINEMETA}/catalog/movie/top/search={quote(query)}.json")
        data  = req.json()
        metas = data.get('metas', [])

        return [
            SearchResult(
                title  = item['name'],
                url    = f"{item['type']}/{item['id']}",
                poster = item.get('poster')
            )
                for item in metas
        ]

    async def load_item(self, url: str) -> MovieInfo | SeriesInfo:
        """Load detailed metadata for a specific Movie or Series"""
        _type, _id = url.split("/")
        req  = await self.httpx.get(f"{self.CINEMETA}/meta/{_type}/{_id}.json")
        data = req.json()
        meta = data.get('meta', {})

        # Parsing duration using regex
        duration = 0
        if runtime := meta.get('runtime'):
            if match := re.search(r"(\d+)", str(runtime)):
                duration = int(match.group(1))

        # Core data structure
        content = {
            "url"         : url,
            "title"       : meta.get('name'),
            "poster"      : meta.get('poster'),
            "description" : meta.get('description'),
            "year"        : str(meta.get('year', '')),
            "rating"      : str(meta.get('imdbRating', '')),
            "tags"        : meta.get('genres', [])
        }

        if _type == "series":
            episodes = [
                Episode(
                    season  = ep.get('season'),
                    episode = ep.get('number', ep.get('episode')),
                    title   = ep.get('title', f"S{ep.get('season')} E{ep.get('number', ep.get('episode', ''))}"),
                    url     = f"series/{ep['id']}"
                )
                    for ep in meta.get('videos', [])
            ]
            return SeriesInfo(**content, episodes=episodes)

        return MovieInfo(**content, duration=duration, actors=meta.get('cast', []))

    async def _fetch_from_provider(self, base_url: str, provider_name: str, _type: str, _id: str) -> list[ExtractResult]:
        """Helper to fetch and extract streams from a Stremio addon provider"""
        try:
            req = await self.httpx.get(f"{base_url}/stream/{_type}/{_id}.json", timeout=10.0)
            if req.status_code != 200:
                return []

            tasks = []
            for s in req.json().get('streams', []):
                # Resolve stream URL (prefer direct url, then externalUrl, then YouTube ID)
                source_url = s.get('url') or s.get('externalUrl') or (f"https://www.youtube.com/watch?v={s['ytId']}" if 'ytId' in s else None)
                if not source_url:
                    continue

                # Filter out obvious premium / ad links (especially for NoTorrent)
                if any(x in source_url for x in ["paypal.com", "nuvio.tv"]):
                    continue

                # Get name/title, prioritizing name then title
                display_name = s.get('name') or s.get('title') or 'Source'

                tasks.append(self.extract(
                    url           = source_url,
                    name_override = f"[{provider_name}] {display_name}"
                ))

            if not tasks:
                return []

            results = await asyncio.gather(*tasks, return_exceptions=True)

            links = []
            for res in results:
                if isinstance(res, Exception):
                    continue
                if isinstance(res, list):
                    links.extend(res)
                elif res:
                    links.append(res)
            return links
        except Exception:
            return []

    async def load_links(self, url: str) -> list[ExtractResult]:
        """Fetch and extract stream links from Streailer and NoTorrent addons"""
        _type, _id = url.split("/")

        results = await asyncio.gather(
            self._fetch_from_provider(self.STREAILER, "Streailer", _type, _id),
            self._fetch_from_provider(self.NOTORRENT, "NoTorrent", _type, _id),
            return_exceptions=True
        )

        links = []
        for res in results:
            if isinstance(res, list):
                links.extend(res)
        return links
