from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import logging

from yt_dlp import YoutubeDL
from yt_dlp.utils import YoutubeDLError
from rich import print, get_console
from rich.live import Live
from rich.console import Group
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
    MofNCompleteColumn,
    TaskID,
)

from ..episode import Episode
from ..langs import LANG


logger = logging.getLogger(__name__)
console = get_console()
download_progress = Progress(
    TextColumn("[bold blue]{task.fields[episode_name]}", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "•",
    TransferSpeedColumn(),
    "•",
    TimeRemainingColumn(),
    console=console,
)
total_progress = Progress(
    TextColumn("[bold cyan]{task.description}"),
    BarColumn(bar_width=None),
    MofNCompleteColumn(),
    TimeRemainingColumn(),
    console=console,
)
progress = Group(total_progress, download_progress)


def download(
    episode: Episode,
    path: Path,
    prefer_languages: list[LANG] = ["VO"],
    concurrent_fragment_downloads=3,
):
    if not any(episode.languages.values()):
        print("[red]No player available")
        return

    me = download_progress.add_task("download", episode_name=episode.name, total=None)
    task = download_progress.tasks[me]

    full_path = (
        path / episode.serie_name / episode.season_name / episode.name
    ).expanduser()

    def hook(data: dict):
        if data.get("status") != "downloading":
            return

        task.total = data.get("total_bytes") or data.get("total_bytes_estimate")
        download_progress.update(me, completed=data.get("downloaded_bytes", 0))

    option = {
        "outtmpl": {"default": f"{full_path}.%(ext)s"},
        "concurrent_fragment_downloads": concurrent_fragment_downloads,
        "progress_hooks": [hook],
        "logger": logger,
    }

    for player in episode.consume_player(prefer_languages):
        try:
            with YoutubeDL(option) as ydl:  # type: ignore
                error_code: int = ydl.download([player])  # type: ignore
        except YoutubeDLError:
            continue

        if not error_code:
            break

        logger.fatal(error_code)

    download_progress.update(me, visible=False)
    if total_progress.tasks:
        total_progress.update(TaskID(0), advance=1)


def multi_download(
    episodes: list[Episode],
    path: Path,
    concurrent_downloads,
    prefer_languages: list[LANG] = ["VO"],
):
    """
    Not sure if you can use this function multiple times
    """
    total_progress.add_task("Downloaded", total=len(episodes))
    with Live(progress, console=console):
        with ThreadPoolExecutor(max_workers=concurrent_downloads["video"]) as executor:
            for episode in episodes:
                executor.submit(
                    download,
                    episode,
                    path,
                    prefer_languages,
                    concurrent_downloads["fragment"],
                )
