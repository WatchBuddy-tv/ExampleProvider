# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

import sys, os
from asyncio      import run
from random       import choice
from time         import time
from pydantic     import ValidationError
from rich.console import Console
from rich.table   import Table
from rich.panel   import Panel
from rich.text    import Text
from rich.box     import ROUNDED, HEAVY_EDGE, SIMPLE_HEAD
from rich.align   import Align
from rich.live    import Live

# Ensure current directory is in path and models are accessible
sys.path.append(os.getcwd())

from KekikStream.Core import (
    PluginManager,
    MainPageResult,
    SearchResult,
    MovieInfo,
    SeriesInfo,
    ExtractorManager,
    ExtractResult
)
from FastAPI import PROXIES

# Premium Color Palette
C_BRAND     = "#00FF88"  # WatchBuddy Green
C_INFO      = "dodger_blue1"
C_WARN      = "orange3"
C_ERR       = "bright_red"
C_SUCCESS   = "spring_green3"
C_HIGHLIGHT = "medium_purple1"
C_MUTED     = "grey50"

console = Console()

class ProviderValidator:
    """A premium validation suite for WatchBuddy Providers using Pydantic."""

    def __init__(self, plugin_dir="Stream/Plugins"):
        self.ext_manager = ExtractorManager(extractor_dir="Stream/Extractors")
        self.manager     = PluginManager(plugin_dir=plugin_dir, ex_manager=self.ext_manager, proxy=PROXIES)
        self.results     = {}
        self.start_time  = time()

    def _header(self):
        banner = Text.assemble(
            ("\n", "default"),
            (" ⚡ ", C_BRAND),
            ("WATCHBUDDY", f"bold {C_BRAND}"),
            (" PROVIDER SDK ", "white"),
            ("v1.2", f"italic {C_MUTED}"),
            ("\n", "default")
        )
        console.print(Align.center(Panel(banner, style=f"bold {C_BRAND}", box=HEAVY_EDGE, expand=False)))

    def _validate_schema(self, obj, model_cls) -> tuple[bool, str]:
        if not obj:
            return False, "Empty Object"
        if not isinstance(obj, model_cls):
            return False, f"Type Mismatch: Expected {model_cls.__name__}, got {type(obj).__name__}"
        try:
            model_cls(**obj.model_dump())
            return True, "Schema OK"
        except ValidationError as e:
            errors = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            return False, f"Schema Error: {', '.join(errors)}"
        except Exception as e:
            return False, f"Validation Failed: {str(e)}"

    def _display_data_list(self, title: str, items: list, model_cls, icon: str = "📂"):
        table = Table(
            show_header  = True,
            header_style = f"bold {C_INFO}",
            border_style = C_MUTED,
            box          = ROUNDED,
            expand       = False,
            padding      = (0, 1)
        )
        table.add_column("#", justify="right", style=C_MUTED)
        table.add_column("Title", style=f"bold {C_SUCCESS}")
        table.add_column("Schema", justify="center")
        table.add_column("Poster", justify="center")
        table.add_column("URL", style=C_INFO, no_wrap=True)

        for i, item in enumerate(items[:5], 1):
            valid, msg = self._validate_schema(item, model_cls)
            status = "[bold green]PASS[/]" if valid else f"[bold red]FAIL:[/] {msg}"
            p_status = "[bold green]YES[/]" if getattr(item, 'poster', None) else "[bold red]NO[/]"
            table.add_row(str(i), item.title, status, p_status, item.url)

        if len(items) > 5:
            table.add_row("...", f"[italic]and {len(items)-5} more content...[/]", "➖", "")

        console.print(Align.center(Panel(table, title=f"[{C_HIGHLIGHT}]{icon} {title}[/]", border_style=C_MUTED, expand=False)))

    async def test_get_main_page(self, plugin) -> dict:
        result = {"status": "❌", "message": "", "data": None}
        try:
            if not plugin.main_page:
                return {"status": "⚠️", "message": "Metadata: Missing main_page dict"}

            url, category = choice(list(plugin.main_page.items()))
            console.print(f"  [{C_MUTED}]Testing Protocol:[/] [bold {C_HIGHLIGHT}]{category}[/]")
            items = await plugin.get_main_page(1, url, category)

            if not items:
                return {"status": "⚠️", "message": f"Discovery: Zero items in {category}"}

            self._display_data_list(f"Curated Discovery: {category}", items, MainPageResult, "✨")
            result.update({"status": "✅", "message": f"Discovery: {len(items)} items", "data": choice(items)})
        except Exception as e:
            result["message"] = f"Discovery Error: {str(e)}"
        return result

    async def test_search(self, plugin, query: str = "A") -> dict:
        result = {"status": "❌", "message": "", "data": None}
        try:
            items = await plugin.search(query)
            if not items:
                items = await plugin.search("The") # Fallback

            if not items:
                return {"status": "⚠️", "message": f"Search: No results for '{query}'"}

            self._display_data_list(f"Universal Search: '{query}'", items, SearchResult, "🔍")
            result.update({"status": "✅", "message": f"Search: {len(items)} results", "data": choice(items)})
        except Exception as e:
            result["message"] = f"Search Error: {str(e)}"
        return result

    async def test_load_item(self, plugin, test_url: str) -> dict:
        result = {"status": "❌", "message": "", "data": None}
        try:
            item = await plugin.load_item(test_url)
            if not item:
                return {"status": "❌", "message": "Metadata: Empty response"}

            # Schema Check
            model_cls = SeriesInfo if isinstance(item, SeriesInfo) else MovieInfo
            valid, msg = self._validate_schema(item, model_cls)
            if not valid:
                return {"status": "❌", "message": f"Schema Violation: {msg}"}

            # Metadata Visual
            grid = Table.grid(expand=False, padding=(0, 2))
            grid.add_column(style=f"bold {C_INFO}", width=12)
            grid.add_column()

            fields = [
                ('title', '💎'), ('url', '🔗'), ('poster', '🖼'),
                ('year', '📅'), ('rating', '⭐'), ('duration', '⏱'),
                ('actors', '🎭'), ('tags', '🏷'), ('description', '📝')
            ]
            for field, icon in fields:
                val = getattr(item, field, None)
                if field == 'description' and val:
                    val = val.strip()

                color = C_SUCCESS if val else C_WARN
                grid.add_row(f"{icon} {field.capitalize()}", f": [{color}]{val or 'NOT SPECIFIED'}[/]")

            ep_count = len(item.episodes) if isinstance(item, SeriesInfo) else 0
            type_tag = f"[bold on {C_HIGHLIGHT}] SERIES [/] [{ep_count} EPISODES]" if ep_count > 0 else f"[bold on {C_INFO}] MOVIE [/]"

            # Create a combined display if it's a series
            metadata_panel = Panel(
                grid,
                title        = f"{type_tag} [bold white]{item.title}[/]",
                subtitle     = f"[{C_MUTED}]{item.url}[/]",
                border_style = C_HIGHLIGHT,
                box          = ROUNDED,
                padding      = (1, 4),
                expand       = False
            )

            if ep_count > 0:
                ep_table = Table(show_header=True, header_style=f"bold {C_INFO}", box=ROUNDED, border_style=C_MUTED, expand=False)
                ep_table.add_column("S", justify="center", style=C_HIGHLIGHT)
                ep_table.add_column("E", justify="center", style=C_HIGHLIGHT)
                ep_table.add_column("Episode Title", style=C_SUCCESS)
                ep_table.add_column("URL", style=C_INFO, no_wrap=True)

                # Show first 3 and last 1 episodes if too many
                display_eps = item.episodes
                if ep_count > 5:
                    for ep in item.episodes[:3]:
                        ep_table.add_row(str(ep.season), str(ep.episode), ep.title, ep.url)
                    ep_table.add_row("..", "..", "[italic]... nested episodes ...[/]", "...")
                    ep = item.episodes[-1]
                    ep_table.add_row(str(ep.season), str(ep.episode), ep.title, ep.url)
                else:
                    for ep in item.episodes:
                        ep_table.add_row(str(ep.season), str(ep.episode), ep.title, ep.url)

                console.print(Align.center(metadata_panel))
                console.print(Align.center(Panel(ep_table, title=f"[{C_SUCCESS}]📋 Episode List ({ep_count})[/]", border_style=C_MUTED, expand=False)))
            else:
                console.print(Align.center(metadata_panel))

            result.update({"status": "✅", "message": "Metadata: OK", "data": item})
        except Exception as e:
            result["message"] = f"Metadata Error: {str(e)}"
        return result

    async def test_load_links(self, plugin, test_url: str) -> dict:
        result = {"status": "❌", "message": "", "data": None}
        try:
            links = await plugin.load_links(test_url)
            if not links:
                return {"status": "⚠️", "message": "Streams: No links found"}

            table = Table(show_header=True, header_style=f"bold {C_INFO}", box=ROUNDED, border_style=C_MUTED, expand=False)
            table.add_column("Provider", style=C_SUCCESS)
            table.add_column("Format", justify="center")
            table.add_column("Schema", justify="center")
            table.add_column("Subtitle", justify="center")
            table.add_column("Direct Stream Path", style=C_INFO, no_wrap=True, width=50) # Limited width for better aesthetics

            for link in links:
                valid, msg = self._validate_schema(link, ExtractResult)
                s_icon = "[bold green]OK[/]" if valid else "[bold red]ERR[/]"
                fmt    = "[bold cyan]HLS[/]" if ".m3u8" in link.url.lower() else "[bold blue]MP4[/]"
                subs   = f"[bold green]YES[/] ({len(link.subtitles)})" if link.subtitles else f"[{C_MUTED}]NO[/]"
                table.add_row(link.name, fmt, s_icon, subs, link.url)

            console.print(Align.center(Panel(table, title=f"[{C_HIGHLIGHT}]🔌 Resolved Stream Sources[/]", border_style=C_MUTED, expand=False)))
            result.update({"status": "✅", "message": f"Streams: {len(links)} sources"})
        except Exception as e:
            result["message"] = f"Stream Error: {str(e)}"
        return result

    async def validate_plugin(self, plugin_name: str):
        console.rule(f"[bold {C_INFO}] PROVIDER SESSION: {plugin_name} [/]", style=C_MUTED)
        plugin = self.manager.select_plugin(plugin_name)
        if not plugin:
            console.print(Align.center(f"[{C_ERR}]Critical Error: Plugin '{plugin_name}' failed to load![/]"))
            return

        report = {"name": plugin_name, "steps": {}}

        test_flow = [
            ("main",   "get_main_page", self.test_get_main_page(plugin)),
            ("search", "search",    self.test_search(plugin)),
        ]

        last_data = None
        for key, label, coro in test_flow:
            console.print(f"\n [bold white]● {label}[/]")
            res = await coro
            report["steps"][key] = res["status"]
            if res.get("data"):
                last_data = res["data"]
            if res["status"] != "✅":
                console.print(f"   {res['status']} {res['message']}")

        if last_data:
            console.print(f"\n [bold white]● load_item[/]")
            res = await self.test_load_item(plugin, last_data.url)
            report["steps"]["item"] = res["status"]

            if res["status"] == "✅":
                link_url = last_data.url
                if isinstance(res["data"], SeriesInfo) and res["data"].episodes:
                    link_url = choice(res["data"].episodes).url

                console.print(f"\n [bold white]● load_links[/]")
                res_link = await self.test_load_links(plugin, link_url)
                report["steps"]["links"] = res_link["status"]

        self.results[plugin_name] = report

    def print_summary(self):
        elapsed = round(time() - self.start_time, 2)
        console.print("\n")
        console.rule(f"[{C_SUCCESS}] ✨ PROOF OF QUALITY REPORT ✨ [/]", style=C_BRAND)

        table = Table(show_header=True, header_style=f"bold {C_INFO}", border_style=C_BRAND, box=ROUNDED, expand=False)
        table.add_column("Provider Name", style=f"bold {C_INFO}", width=25)
        table.add_column("Discovery", justify="center", width=12)
        table.add_column("Search", justify="center", width=12)
        table.add_column("Metadata", justify="center", width=12)
        table.add_column("Streams", justify="center", width=12)

        for name, rep in self.results.items():
            s = rep["steps"]
            table.add_row(
                name,
                s.get("main", "➖"),
                s.get("search", "➖"),
                s.get("item", "➖"),
                s.get("links", "➖")
            )

        console.print(Align.center(table))
        footer = Text.assemble(
            (f"Analytics Ready  •  ", C_MUTED),
            ("✅ SUCCESS ", C_SUCCESS), ("⚠️ PARTIAL ", C_WARN), ("❌ CRITICAL ", C_ERR),
            (f"  •  Time: {elapsed}s", C_MUTED)
        )
        console.print(Align.center(footer))
        console.print("\n")

async def main():
    validator = ProviderValidator()
    validator._header()
    names = validator.manager.get_plugin_names()

    if len(sys.argv) > 1:
        targets = sys.argv[1].split(",")
        for t in targets:
            if t in names:
                await validator.validate_plugin(t)
            else:
                console.print(Align.center(f"[{C_ERR}]Error: Target '{t}' not found.[/]"))
    else:
        for name in names:
            await validator.validate_plugin(name)

    validator.print_summary()

if __name__ == "__main__":
    run(main())
