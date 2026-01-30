# This tool was written by @keyiflerolsun | for @KekikAkademi

from KekikStream.Core import PluginBase, MainPageResult, SearchResult, MovieInfo, SeriesInfo, ExtractResult, HTMLHelper
import asyncio

class RareFilmm(PluginBase):
    """
    RareFilmm Plugin Implementation
    Website: https://rarefilmm.com
    Category: Rare and Classic Cinema
    """
    name        = "RareFilmm"
    language    = "en"
    main_url    = "https://rarefilmm.com"
    favicon     = f"https://www.google.com/s2/favicons?domain={main_url}&sz=64"
    description = "A sophisticated platform dedicated to rare and classic world cinema."

    # Define main page categories for navigation within WatchBuddy
    main_page = {
        f"{main_url}/page/"                           : "LATESTS",
        f"{main_url}/category/action/page/"           : "ACTION",
        f"{main_url}/category/adventure/page/"        : "ADVENTURE",
        f"{main_url}/category/animation/page/"        : "ANIMATION",
        f"{main_url}/category/arthouse/page/"         : "ARTHOUSE",
        f"{main_url}/category/biography/page/"        : "BIOGRAPHY",
        f"{main_url}/category/blaxploitation/page/"   : "BLAXPLOITATION",
        f"{main_url}/category/camp/page/"             : "CAMP",
        f"{main_url}/tag/christmas/page/"             : "CHRISTMAS",
        f"{main_url}/category/comedy/page/"           : "COMEDY",
        f"{main_url}/category/cult/page/"             : "CULT",
        f"{main_url}/category/documentary/page/"      : "DOCUMENTARY",
        f"{main_url}/category/drama/page/"            : "DRAMA",
        f"{main_url}/category/epic/page/"             : "EPIC",
        f"{main_url}/category/erotic/page/"           : "EROTIC",
        f"{main_url}/category/eurospy/page/"          : "EUROSPY",
        f"{main_url}/category/experimental/page/"     : "EXPERIMENTAL",
        f"{main_url}/category/exploitation/page/"     : "EXPLOITATION",
        f"{main_url}/category/family/page/"           : "FAMILY",
        f"{main_url}/category/fantasy/page/"          : "FANTASY",
        f"{main_url}/category/film-noir/page/"        : "FILM NOIR",
        f"{main_url}/category/giallo/page/"           : "GIALLO",
        f"{main_url}/category/horror/page/"           : "HORROR",
        f"{main_url}/category/mini-series/page/"      : "MINI-SERIES",
        f"{main_url}/category/music/page/"            : "MUSIC",
        f"{main_url}/category/musical/page/"          : "MUSICAL",
        f"{main_url}/category/mystery/page/"          : "MYSTERY",
        f"{main_url}/category/neo-noir/page/"         : "NEO-NOIR",
        f"{main_url}/category/peplum/page/"           : "PEPLUM",
        f"{main_url}/category/politics/page/"         : "POLITICS",
        f"{main_url}/category/pre-code/page/"         : "PRE-CODE",
        f"{main_url}/category/sci-fi/page/"           : "SCI-FI",
        f"{main_url}/category/short/page/"            : "SHORT",
        f"{main_url}/category/silent/page/"           : "SILENT",
        f"{main_url}/category/spaghetti-western/page/": "SPAGHETTI WESTERN",
        f"{main_url}/category/sport/page/"            : "SPORT",
        f"{main_url}/category/television/page/"       : "TELEVISION",
        f"{main_url}/category/theatre/page/"          : "THEATRE",
        f"{main_url}/category/thriller/page/"         : "THRILLER",
        f"{main_url}/category/tv-movie/page/"         : "TV MOVIE",
        f"{main_url}/category/WAR/page/"              : "WAR",
        f"{main_url}/category/western/page/"          : "WESTERN",
    }

    async def get_main_page(self, page: int, url: str, category: str) -> list[MainPageResult]:
        """
        Fetches and parses the main gallery items based on the provided category URL.
        """
        response = await self.httpx.get(f"{url}{page}")
        helper   = HTMLHelper(response.text)

        results  = []
        for item in helper.select("div.post"):
            title  = helper.select_text("h2 a", item)
            href   = helper.select_attr("h2 a", "href", item)

            poster_style = helper.select_attr("div.featured-image", "style") or ""
            poster_match = helper.regex_first(r"url\((.*?)\)", poster_style)
            poster       = poster_match.strip("'").strip('"') if poster_match else None

            if title and href:
                results.append(MainPageResult(
                    category = category,
                    title    = self.clean_title(title),
                    url      = self.fix_url(href),
                    poster   = self.fix_url(poster)
                ))

        return results

    async def search(self, query: str) -> list[SearchResult]:
        """
        Executes a remote search on the provider website.
        """
        response = await self.httpx.get(f"{self.main_url}?s={query}")
        helper   = HTMLHelper(response.text)

        results  = []
        for item in helper.select("div.post"):
            title  = helper.select_text("h2 a", item)
            href   = helper.select_attr("h2 a", "href", item)

            poster_style = helper.select_attr("div.featured-image", "style") or ""
            poster_match = helper.regex_first(r"url\((.*?)\)", poster_style)
            poster       = poster_match.strip("'").strip('"') if poster_match else None

            if title and href:
                results.append(SearchResult(
                    title  = self.clean_title(title),
                    url    = self.fix_url(href),
                    poster = self.fix_url(poster)
                ))

        return results

    async def load_item(self, url: str) -> MovieInfo | SeriesInfo:
        """
        Retrieves detailed metadata for a specific media content.
        """
        response = await self.httpx.get(url)
        helper   = HTMLHelper(response.text)

        title       = helper.select_text("h1.entry-title")
        description = helper.select_text("div.entry-content p")
        tags        = helper.select_texts("div.entry-tags a")

        # Extract additional metadata using HTMLHelper capabilities
        rating = helper.select_text("span.js-rmp-avg-rating")
        year   = helper.extract_year("h1.entry-title")
        actors = helper.meta_list("Stars:")

        poster_style = helper.select_attr("div.featured-image", "style") or ""
        poster_match = helper.regex_first(r"url\((.*?)\)", poster_style)
        poster       = poster_match.strip("'").strip('"') if poster_match else None

        return MovieInfo(
            url         = url,
            title       = self.clean_title(title),
            poster      = self.fix_url(poster),
            description = description,
            tags        = tags,
            rating      = rating,
            year        = year,
            actors      = actors
        )

    async def load_links(self, url: str) -> list[ExtractResult]:
        """
        Identifies and yields playable video sources (embeds or direct streams).
        """
        response = await self.httpx.get(url)
        helper   = HTMLHelper(response.text)

        tasks    = []

        # 1. Primary Source (Embedded Iframe)
        iframe_src = helper.select_attr("article iframe", "src")
        if iframe_src:
            tasks.append(self.extract(
                url     = self.fix_url(iframe_src),
                referer = f"{self.main_url}/",
                prefix  = "Primary Source"
            ))

        # 2. Alternative Sources (Download Options)
        # Extract links from 'a' tags that contain 'DL via' or similar patterns
        for link_el in helper.select("article a"):
            href = helper.select_attr(None, "href", link_el)
            text = helper.select_text(None, link_el)

            if not href or not any(x in text for x in ["DL via", "Download"]):
                continue

            tasks.append(self.extract(
                url     = self.fix_url(href),
                referer = f"{self.main_url}/",
                prefix  = text.replace("⇒", "").strip()
            ))

        if not tasks:
            return []

        # Perform extractions in parallel for better performance
        extracted_results = await asyncio.gather(*tasks)

        links = []
        for res in extracted_results:
            if isinstance(res, list):
                links.extend(res)
            elif res:
                links.append(res)

        return links
