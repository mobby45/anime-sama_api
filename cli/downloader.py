import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import logging

from yt_dlp import YoutubeDL
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

sys.path.append("../anime_sama_api")
from anime_sama_api.episode import Episode


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
    concurrent_fragment_downloads=3,
):
    if episode.languages.best is None:
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

    with YoutubeDL(option) as ydl:  # type: ignore
        error_code: int = ydl.download([episode.languages.best])  # type: ignore

    if error_code:
        return

    download_progress.update(me, visible=False)
    if total_progress.tasks:
        total_progress.update(TaskID(0), advance=1)


def multi_download(episodes: list[Episode], path: Path, concurrent_downloads):
    """
    Not sure if you can use this function multiple times
    """
    total_progress.add_task("Downloaded", total=len(episodes))
    with Live(progress, console=console):
        with ThreadPoolExecutor(max_workers=concurrent_downloads["video"]) as executor:
            for episode in episodes:
                executor.submit(
                    download, episode, path, concurrent_downloads["fragment"]
                )
