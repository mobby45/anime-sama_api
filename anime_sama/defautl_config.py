from pathlib import Path

PREFER_VF = False
INTERNAL_PLAYER_COMMAND = "mpv".split()
DOWNLOAD_PATH = Path("~/Downloads/Anime-Sama")
DOWNLOAD = True

URL = "https://anime-sama.fr/"

# fmt: off
PLAYERS = {
    "prefer": [],
    "ban": ["myvid", "myvi", "anime-sama"]
}

# fmt: off
CONCURRENT_DOWNLOADS = {
    "fragment": 3,
    "video": 5
}
