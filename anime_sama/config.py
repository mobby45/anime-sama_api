from defautl_config import *
from pathlib import Path

PREFER_VF = True
INTERNAL_PLAYER_COMMAND = "mpv".split()
DOWNLOAD_PATH = Path("~/Downloads/Anime-Sama")

URL = "https://anime-sama.fr/"

# fmt: off
PLAYERS = {
    "prefer": ["anime-sama"],
    "ban": [""]
}

# fmt: off
CONCURRENT_DOWNLOADS = {
    "fragment": 3,
    "video": 5
}
