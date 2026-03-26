# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from KekikStream.Core import PluginBase, MainPageResult, SearchResult, MovieInfo, ExtractResult
from json             import dumps, loads
from re               import compile, MULTILINE
from contextlib       import suppress
from urllib.parse     import unquote_plus

class CanliTV(PluginBase):
    name        = "CanliTV"
    language    = "tr"
    main_url    = "https://codeberg.org/ramazansancar/streams-tr/raw/branch/main/list.m3u"
    favicon     = "https://www.google.com/s2/favicons?domain=codeberg.org&sz=64"
    description = "Türkiye odaklı canlı TV M3U listesi."

    main_page = {"all": "Tümü"}

    extinf_re     = compile(r'#EXTINF:-1(.*?),(.*)$')
    group_re      = compile(r'group-title="([^"]+)"')
    logo_re       = compile(r'tvg-logo="([^"]+)"')
    language_re   = compile(r'tvg-language="([^"]+)"')
    country_re    = compile(r'tvg-country="([^"]+)"')
    channel_id_re = compile(r'tvg-id="([^"]+)"')
    url_re        = compile(r'^(https?://[^\s]+)', MULTILINE)
    user_agent_re = compile(r'#EXTVLCOPT:http-user-agent=(.*)')
    referer_re    = compile(r'#EXTVLCOPT:http-referrer=(.*)')

    @staticmethod
    def _encode(obj: dict) -> str:
        """Dict'i boşluksuz kompakt JSON string'e dönüştürür."""
        return dumps(obj, ensure_ascii=False, separators=(',', ':'))

    @staticmethod
    def _decode(url: str) -> dict | None:
        """JSON string'i parse eder; çift URL-encoding'e karşı gerektiğinde iki kez unquote dener."""
        current = unquote_plus(url)
        with suppress(Exception):
            return loads(current)
        current = unquote_plus(current)
        with suppress(Exception):
            return loads(current)
        return None

    async def _get_playlist(self) -> list[dict]:
        istek = await self.httpx.get(self.main_url)
        istek.raise_for_status()

        playlist   = []
        extinf_raw = None
        title      = None
        user_agent = None
        referer    = None

        for ham_satir in istek.text.splitlines():
            satir = ham_satir.strip()
            if not satir:
                continue

            if extinf_eslesme := self.extinf_re.search(satir):
                extinf_raw = extinf_eslesme.group(1)
                title      = extinf_eslesme.group(2).strip() or "İsimsiz Kanal"
                user_agent = None
                referer    = None
                continue

            if ua_eslesme := self.user_agent_re.search(satir):
                user_agent = ua_eslesme.group(1).strip() or None
                continue

            if ref_eslesme := self.referer_re.search(satir):
                referer = ref_eslesme.group(1).strip() or None
                continue

            if not extinf_raw or not title:
                continue

            if url_eslesme := self.url_re.search(satir):
                grup = self.group_re.search(extinf_raw)
                logo = self.logo_re.search(extinf_raw)
                dil  = self.language_re.search(extinf_raw)
                ulke = self.country_re.search(extinf_raw)
                kim  = self.channel_id_re.search(extinf_raw)

                playlist.append({
                    "title"      : title,
                    "group"      : (grup.group(1).strip() if grup else "Diğer") or "Diğer",
                    "poster"     : logo.group(1).strip() if logo else None,
                    "language"   : dil.group(1).strip() if dil else None,
                    "country"    : ulke.group(1).strip() if ulke else None,
                    "channel_id" : kim.group(1).strip() if kim else None,
                    "url"        : url_eslesme.group(1).strip(),
                    "user_agent" : user_agent,
                    "referer"    : referer,
                })

                extinf_raw = None
                title      = None
                user_agent = None
                referer    = None

        kategoriler = ["all"]
        for kanal in playlist:
            grup = kanal["group"]
            if grup not in kategoriler:
                kategoriler.append(grup)

        dinamik_main_page = {"all": "Tümü"}
        dinamik_main_page.update({kategori: kategori for kategori in kategoriler if kategori != "all"})

        self.main_page           = dinamik_main_page
        self.__class__.main_page = dict(dinamik_main_page)

        return playlist

    async def get_main_page(self, page: int, url: str, category: str) -> list[MainPageResult]:
        channels = await self._get_playlist()
        channels = channels if url == "all" else [kanal for kanal in channels if kanal["group"] == url]

        start = max(page - 1, 0) * 24
        end   = start + 24

        return [
            MainPageResult(
                category = category,
                title    = kanal["title"],
                url      = self._encode(kanal),
                poster   = kanal["poster"],
            )
                for kanal in channels[start:end]
        ]

    async def search(self, query: str) -> list[SearchResult]:
        playlist = await self._get_playlist()
        query    = query.casefold().strip()

        if not query:
            return []

        sonuclar = []
        for kanal in playlist:
            alanlar = [
                kanal["title"],
                kanal.get("group") or "",
                kanal.get("language") or "",
                kanal.get("country") or "",
                kanal.get("channel_id") or "",
            ]

            if any(query in alan.casefold() for alan in alanlar):
                sonuclar.append(SearchResult(
                    title  = kanal["title"],
                    url    = self._encode(kanal),
                    poster = kanal["poster"],
                ))

        return sonuclar[:50]

    async def load_item(self, url: str) -> MovieInfo:
        kanal_url = url
        kanal     = self._decode(url)

        if not kanal:
            kanal = next((item for item in await self._get_playlist() if item["url"] == url), None)
            if kanal:
                kanal_url = self._encode(kanal)

        if not kanal:
            return MovieInfo(
                url         = url,
                title       = "Canlı Yayın",
                description = "Playlist üzerinde bulunamayan canlı yayın girdisi.",
                tags        = "Canlı TV, IPTV",
                year        = "LIVE",
            )

        aciklama = f"{kanal['group']} kategorisinden canlı yayın."
        if kanal.get("language"):
            aciklama += f" Dil: {kanal['language']}."
        if kanal.get("country"):
            aciklama += f" Ülke: {kanal['country']}."

        etiketler = [kanal["group"], "Canlı TV", "IPTV"]
        if kanal.get("language"):
            etiketler.append(kanal["language"])
        if kanal.get("country"):
            etiketler.append(kanal["country"])

        return MovieInfo(
            url         = kanal_url,
            title       = kanal["title"],
            poster      = kanal["poster"],
            description = aciklama,
            tags        = ", ".join(etiketler),
            year        = "LIVE",
        )

    async def load_links(self, url: str) -> list[ExtractResult]:
        kanal = self._decode(url)
        if not kanal:
            kanal = {"title": "Canlı Yayın", "url": url}

        return [
            ExtractResult(
                name       = f"{kanal.get('title', 'Canlı Yayın')} - HLS",
                url        = kanal["url"],
                referer    = kanal.get("referer"),
                user_agent = kanal.get("user_agent"),
            )
        ]
