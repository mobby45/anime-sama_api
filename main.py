import asyncio
import logging

from rich import get_console
from rich.logging import RichHandler

import cli.config as config
import cli.downloader as downloader
import cli.internal_player as internal_player
from cli.utils import safe_input, select_one, select_range, keyboard_inter
from cli.custom_client import CustomAsyncClient

from anime_sama_api.top_level import AnimeSama

console = get_console()
console._highlight = False
logging.basicConfig(format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
spinner = lambda text: console.status(text, spinner_style="cyan")


async def main():
    query = safe_input("Anime name: \033[0;34m", str)

    with spinner(f"Searching for [blue]{query}"):
        catalogues = await AnimeSama(config.URL, CustomAsyncClient()).search(query)
    catalogue = select_one(catalogues)

    with spinner(f"Getting season list for [blue]{catalogue.name}"):
        seasons = await catalogue.seasons()
    season = select_one(seasons)

    with spinner(f"Getting episode list for [blue]{season.name}"):
        episodes = await season.episodes()

    console.print(f"\n[cyan bold underline]{season.serie_name} - {season.name}")
    selected_episodes = select_range(
        episodes, msg="Choose episode(s)", print_choices=True
    )

    for episode in selected_episodes:
        episode.languages.prefer_languages = config.PREFER_LANGUAGES
        episode.languages.set_best(config.PLAYERS["prefer"], config.PLAYERS["ban"])

    # print(selected_episodes[0].languages.best)
    if config.DOWNLOAD:
        downloader.multi_download(
            selected_episodes, config.DOWNLOAD_PATH, config.CONCURRENT_DOWNLOADS
        )
    else:
        internal_player.play_episode(selected_episodes[0]).wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.exceptions.CancelledError, EOFError):
        keyboard_inter()
