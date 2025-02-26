from .top_level import AnimeSama
from .catalogue import Catalogue
from .season import Season
from .episode import Episode, Languages, Players
from .langs import Lang, LangId, lang2ids, id2lang, lang_ids, flags

try:
    from .cli.__main__ import main
    from .cli.downloader import download, multi_download
except ImportError:
    import sys

    def main() -> int:
        print(
            "This anime-sama_api function could not run because the required "
            "dependencies were not installed.\nMake sure you've installed "
            "everything with: pip install 'anime-sama_api[cli]'"
        )

        sys.exit(1)

    download = multi_download = main  # type: ignore


# __package__ = "anime-sama_api"
__all__ = [
    "AnimeSama",
    "Catalogue",
    "Season",
    "Players",
    "Languages",
    "Episode",
    "Lang",
    "LangId",
    "lang2ids",
    "id2lang",
    "lang_ids",
    "flags",
    "download",
    "multi_download",
    "main",
]

"""__locals = locals()
for __name in __all__:
    if not __name.startswith("__"):
        setattr(__locals[__name], "__module__", "anime-sama_api")  # noqa"""
