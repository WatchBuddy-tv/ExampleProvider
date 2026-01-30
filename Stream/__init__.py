# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from KekikStream.Core import PluginManager, ExtractorManager, MediaManager, MovieInfo, SeriesInfo
from FastAPI          import PROXIES

extractor_manager = ExtractorManager(extractor_dir="Stream/Extractors")
plugin_manager    = PluginManager(plugin_dir="Stream/Plugins", ex_manager=extractor_manager, proxy=PROXIES)
