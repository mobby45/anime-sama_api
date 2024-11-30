import asyncio

from termcolor import colored
from yaspin import yaspin

import cli.config as config
import cli.downloader as downloader
import cli.internal_player as internal_player
from cli.utils import safe_input, select_one, select_range, put_color, keyboard_inter
from cli.custom_client import CustomAsyncClient

from anime_sama_api.top_level import AnimeSama


async def main():
    query = safe_input("Anime name: " + put_color("blue"), str)
    with yaspin(text=f"Searching for {colored(query, 'blue')}", color="cyan"):
        catalogues = await AnimeSama(config.URL, CustomAsyncClient()).search(query)
    catalogue = select_one(catalogues)

    with yaspin(
        text=f"Getting season list for {colored(catalogue.name, 'blue')}", color="cyan"
    ):
        seasons = await catalogue.seasons()
    season = select_one(seasons)

    with yaspin(
        text=f"Getting episode list for {colored(season.name, 'blue')}", color="cyan"
    ):
        episodes = await season.episodes()

    print(
        colored(
            f"\n{season.serie_name} - {season.name}",
            "cyan",
            attrs=["bold", "underline"],
        )
    )
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
