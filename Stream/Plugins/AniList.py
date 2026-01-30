# This tool was written by @keyiflerolsun | for @KekikAkademi

from KekikStream.Core import PluginBase, MainPageResult, SearchResult, Episode, MovieInfo, SeriesInfo, ExtractResult
import re

class AniList(PluginBase):
    """AniList Wrapper (Discovery & Metadata via GraphQL)"""
    name        = "AniList"
    language    = "en"
    main_url    = "https://anilist.co"
    favicon     = f"https://www.google.com/s2/favicons?domain={main_url}&sz=64"
    description = "Advanced Anime discovery plugin based on GraphQL."

    API_URL = "https://graphql.anilist.co"

    # Expanded Main Page Categories
    main_page = {
        "TRENDING_DESC"  : "Trending Now",
        "POPULAR_DESC"   : "Popular This Season",
        "SCORE_DESC"     : "Top Rated All Time",
        "FAVOURITES_DESC": "Most Favorited",
        "START_DATE_DESC": "New Releases",
        "UPDATED_AT_DESC": "Recently Updated"
    }

    async def _query(self, query: str, variables: dict) -> dict:
        """Helper to send GraphQL queries"""
        req = await self.httpx.post(self.API_URL, json={'query': query, 'variables': variables})
        return req.json().get('data', {}) if req.status_code == 200 else {}

    async def get_main_page(self, page: int, url: str, category: str) -> list[MainPageResult]:
        """Fetch listings from AniList catalogs based on sort type"""
        query = """
        query ($page: Int, $sort: [MediaSort]) {
          Page(page: $page, perPage: 20) {
            media(sort: $sort, type: ANIME, isAdult: false) {
              id
              title { english romaji }
              coverImage { large }
            }
          }
        }
        """
        data = await self._query(query, {'page': page, 'sort': [url]})

        return [
            MainPageResult(
                category = category,
                title    = i['title']['english'] or i['title']['romaji'],
                url      = str(i['id']),
                poster   = i['coverImage']['large']
            )
                for i in data.get('Page', {}).get('media', [])
        ]

    async def search(self, query_str: str) -> list[SearchResult]:
        """Search anime on AniList"""
        query = """
        query ($search: String) {
          Page(perPage: 20) {
            media(search: $search, type: ANIME, isAdult: false) {
              id
              title { english romaji }
              coverImage { large }
            }
          }
        }
        """
        data = await self._query(query, {'search': query_str})

        return [
            SearchResult(
                title  = i['title']['english'] or i['title']['romaji'],
                url    = str(i['id']),
                poster = i['coverImage']['large']
            )
                for i in data.get('Page', {}).get('media', [])
        ]

    async def load_item(self, url: str) -> MovieInfo | SeriesInfo:
        """Fetch detailed metadata and build Episode list"""
        query = """
        query ($id: Int) {
          Media(id: $id) {
            id
            format
            title { english romaji }
            description
            startDate { year }
            averageScore
            genres
            duration
            coverImage { large }
            bannerImage
            episodes
            characters(sort: RELEVANCE, perPage: 10) {
              nodes { name { full } }
            }
            studios(isMain: true) {
              nodes { name }
            }
          }
        }
        """
        data = await self._query(query, {'id': int(url)})
        meta = data.get('Media', {})

        # Cast & Genres + Studios
        actors = [char['name']['full'] for char in meta.get('characters', {}).get('nodes', [])]
        tags   = meta.get('genres', [])
        if meta.get('studios', {}).get('nodes'):
            tags.extend([s['name'] for s in meta['studios']['nodes']])

        desc = re.sub('<[^<]+?>', '', meta.get('description', '')) if meta.get('description') else ''

        # Rating Scaling (AniList 100 -> WatchBuddy 10.0)
        rating = meta.get('averageScore')
        rating_str = f"{rating/10:.1f}" if rating else ""

        # Core Object Data
        veri = {
            "url"         : url,
            "title"       : meta['title']['english'] or meta['title']['romaji'],
            "poster"      : meta['coverImage']['large'],
            "description" : desc,
            "year"        : str(meta.get('startDate', {}).get('year', '')),
            "rating"      : rating_str,
            "tags"        : tags,
            "actors"      : actors,
            "duration"    : meta.get('duration')
        }

        # Format detection
        if meta.get('format') == 'MOVIE':
            return MovieInfo(**veri)

        # Build episodes for Series
        episodes = [
            Episode(
                season  = 1,
                episode = i,
                title   = f"Episode {i}",
                url     = f"{url}/ep/{i}"
            )
                for i in range(1, (meta.get('episodes') or 1) + 1)
        ]
        
        return SeriesInfo(**veri, episodes=episodes)

    async def load_links(self, url: str) -> list[ExtractResult]:
        return []
