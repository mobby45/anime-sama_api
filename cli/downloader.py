import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from termcolor import colored
from yt_dlp import YoutubeDL
from tqdm import tqdm

from .utils import put_color

sys.path.append("../anime_sama_api")
from anime_sama_api.episode import Episode


class OnlyErrorLogger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


class TqdmYoutubeDL(tqdm):
    def __init__(self, *args, **kwargs):
        super().__init__(unit="B", unit_scale=True, mininterval=1, *args, **kwargs)

    def hook(self, data: dict):
        if data.get("status") != "downloading":
            return

        if self.total is None:
            # Resume download
            self.reset()
            self.n = self.last_print_n = data.get("downloaded_bytes", 0)

        self.total = data.get("total_bytes") or data.get("total_bytes_estimate")
        self.update(data.get("downloaded_bytes", 0) - self.n)


def download(
    episode: Episode, path: Path, concurrent_fragment_downloads=3, main_tqdm_bar=None
):
    if episode.languages.best is None:
        print(colored("No player available", "red"))
        return

    full_path = (
        path / episode.serie_name / episode.season_name / episode.name
    ).expanduser()

    with TqdmYoutubeDL(
        desc=put_color("red") + episode.name,
        leave=not bool(main_tqdm_bar),
    ) as tqdm_bar:
        option = {
            "outtmpl": {"default": f"{full_path}.%(ext)s"},
            "concurrent_fragment_downloads": concurrent_fragment_downloads,
            "progress_hooks": [tqdm_bar.hook],
            "logger": OnlyErrorLogger(),
        }

        with YoutubeDL(option) as ydl:  # type: ignore
            ydl.download([episode.languages.best])

    if main_tqdm_bar is not None:
        main_tqdm_bar.update()


def multi_download(episodes: list[Episode], path: Path, concurrent_downloads):
    print(put_color("light_red"), end="")
    with tqdm(total=len(episodes), unit="Ep") as tqdm_bar:
        with ThreadPoolExecutor(max_workers=concurrent_downloads["video"]) as executor:
            executor.map(
                lambda episode: download(
                    episode, path, concurrent_downloads["fragment"], tqdm_bar
                ),
                episodes,
            )
