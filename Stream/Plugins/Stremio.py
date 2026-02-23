# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from KekikStream.Core import PluginBase, MainPageResult, SearchResult, Episode, MovieInfo, SeriesInfo, ExtractResult
from urllib.parse     import quote
import re, asyncio

class Stremio(PluginBase):
    """Stremio Wrapper (Discovery: Cinemeta | Streams: Streailer)"""
    name        = "Stremio"
    language    = "multi"
    main_url    = "https://web.stremio.com"
    favicon     = f"https://www.google.com/s2/favicons?domain={main_url}&sz=64"
    description = "Combined Stremio Wrapper (Cinemeta Catalogs + Streailer Trailers)"

    # API Resources
    CINEMETA  = "https://v3-cinemeta.strem.io"
    STREAILER = "https://9aa032f52161-streailer.baby-beamup.club"

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

    async def load_links(self, url: str) -> list[ExtractResult]:
        """Fetch and extract stream links using Streailer addon"""
        _type, _id = url.split("/")
        req = await self.httpx.get(f"{self.STREAILER}/stream/{_type}/{_id}.json")

        if req.status_code != 200:
            return []

        tasks = []
        for s in req.json().get('streams', []):
            # Resolve stream URL (prefer direct url, then externalUrl, then YouTube ID)
            source_url = s.get('url') or s.get('externalUrl') or (f"https://www.youtube.com/watch?v={s['ytId']}" if 'ytId' in s else None)
            if not source_url:
                continue

            # Pass to extractor manager for link resolution
            tasks.append(self.extract(
                url           = source_url,
                name_override = s.get('name', 'Source')
            ))

        if not tasks:
            return []

        # Execute extractions in parallel
        extracted_results = await asyncio.gather(*tasks)

        links = []
        for res in extracted_results:
            if isinstance(res, list):
                links.extend(res)
            elif res:
                links.append(res)

        return links
