# Anime-Sama Downloader
Download video from anime-sama.fr

# Requirements
- Python 3.10 or higher
- git
- [uv](https://docs.astral.sh/uv/#installation)

# Installation
```bash
git clone https://github.com/Sky-NiniKo/anime-sama_downloader.git
cd anime-sama_downloader
uv sync --extra cli
```

# Run
```bash
uv run anime-sama
```

# Update
In the `anime_sama` folder:
```bash
git pull
```

## Config
You can customize the config at `~/.config/anime-sama_cli/config.toml` for MacOs/Linux and at `~/AppData/Local/anime-sama_cli/config.toml` for Windows.

# Contribution
I am open to contribution. Please only open a PR for ONE change. AKA don't do "Various improvements" and explain your motivation behind your improvement ("Various typos fix"/"Cleanup" is fine).
