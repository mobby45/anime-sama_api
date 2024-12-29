# Anime-Sama Downloader
Download video from anime-sama.fr

# Requirements
- Python 3.12 or higher
- git

# Installation
```bash
git clone https://github.com/Sky-NiniKo/anime-sama_downloader.git
cd anime-sama_downloader
```

If you don't have poetry, `pip install poetry`.
```bash
poetry install --extras cli
```

If you can't install poetry, but be warn, it is not supported:
```bash
pip install -r requirements.txt
```

# Run
Poetry:
```bash
poetry run anime-sama
```
Otherwise:
```bash
anime-sama
```

# Update
In the `anime_sama` folder:
```bash
git pull
```

## Config
You can customize the config in `anime_sama_api/cli/config.py`

```yaml
PREFER_LANGUAGES: list of languages in order of preference see LANG in anime_sama/langs.py for available language
DOWNLOAD_PATH: Where to place downloaded videos
URL: url of anime-sama (You shouldn't touch that)
PLAYERS:
    prefer: player to use if multiple are available (first in the list are prefer over the afters)
    ban: player to not use (even if that the only player)
CONCURRENT_DOWNLOADS:
    fragment: how many fragment of a video to download at once
    video: how many video to download at once
```

# Contribution
I am open to contribution.
