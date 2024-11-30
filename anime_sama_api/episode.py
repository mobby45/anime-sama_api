import re
import logging
from itertools import product
from dataclasses import dataclass, field

from termcolor import colored

from .langs import flags, LANG, LANG_ID, id2lang, lang2ids


logger = logging.getLogger(__name__)


@dataclass
class Players:
    availables: list[str] = field(default_factory=list)
    _best: str | None = field(default=None, init=False)
    index: int = field(default=1, init=False)

    @property
    def best(self) -> str | None:
        if self._best is None:
            self.set_best()
        return self._best

    def set_best(
        self, prefers: list[str] | None = None, bans: list[str] | None = None
    ) -> None:
        if not self.availables:
            return
        if prefers is None:
            prefers = []
        if bans is None:
            bans = []
        for prefer, player in product(prefers, self.availables):
            if prefer in player:
                self._best = player
                return
        for i in range(self.index, len(self.availables) + self.index):
            candidate = self.availables[i % len(self.availables)]
            if all(ban not in candidate for ban in bans):
                self._best = candidate
                return
        logger.warning(
            f"WARNING: No suitable player found. Defaulting to {self.availables[0]}"
        )
        self._best = self.availables[0]


@dataclass
class Languages:
    players_map: dict[LANG_ID, Players]
    prefer_languages: list[LANG] = field(default_factory=list)

    def __post_init__(self):
        if not self.players_map:
            logger.warning(f"WARNING: No player available for {self}")

    @property
    def availables(self) -> dict[LANG, list[Players]]:
        availables: dict[LANG, list[Players]] = {}
        for lang_id, players in self.players_map.items():
            if availables.get(id2lang[lang_id]) is None:
                availables[id2lang[lang_id]] = []
            availables[id2lang[lang_id]].append(players)
        return availables

    @property
    def best(self) -> str | None:
        for prefer_language in self.prefer_languages:
            for players in self.availables.get(prefer_language, []):
                if players.availables:
                    return players.best

        for language in lang2ids:
            for players in self.availables[language]:
                if players.availables:
                    logger.warning(
                        f"WARNING: Language preference not respected. Defaulting to {language}"
                    )
                    return players.best

        return None

    def set_best(self, *args, **kwargs):
        for players in self.players_map.values():
            players.set_best(*args, **kwargs)


@dataclass
class Episode:
    languages: Languages
    serie_name: str = ""
    season_name: str = ""
    episode_name: str = ""
    _index: int = 1

    def __post_init__(self) -> None:
        self.name = self.episode_name
        self.fancy_name = self.name
        for lang in self.languages.availables:
            self.fancy_name += f" {flags[lang]}"

        self.index = self._index
        match_season_number = re.search(r"\d+", self.season_name)
        self.season_number = (
            int(match_season_number.group(0)) if match_season_number else 0
        )
        self.long_name = f"{self.season_name} - {self.episode_name}"
        self.short_name = f"{self.serie_name} S{self.season_number:02}E{self.index:02}"

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, value: int):
        self._index = value
        for players in self.languages.players_map.values():
            players.index = self._index

    def __str__(self):
        return self.fancy_name
