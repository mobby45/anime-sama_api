from ast import literal_eval
from functools import reduce
import re
import asyncio

from httpx import AsyncClient

from .langs import LANG_ID, lang_ids
from .episode import Episode, Players, Languages
from .utils import zip_varlen, split_and_strip


class Season:
    def __init__(
        self,
        url: str,
        name="",
        serie_name="",
        client: AsyncClient | None = None,
    ) -> None:
        self.pages = [url + lang + "/" for lang in lang_ids]
        self.site_url = "/".join(url.split("/")[:3]) + "/"

        self.name = name or url.split("/")[-2]
        self.serie_name = serie_name or url.split("/")[-3]

        self.client = client or AsyncClient()

    async def _get_players_from(self, page: str) -> list[Players]:
        response = await self.client.get(page)

        if not response.is_success:
            return []

        match_url = re.search(r"episodes\.js\?filever=\d+", response.text)
        if not match_url:
            return []

        episodes_url = page + match_url.group(0)
        episodes_js = await self.client.get(episodes_url)

        players_list = episodes_js.text.split("[")[1:]
        players_list_links = (re.findall(r"'(.+?)'", player) for player in players_list)

        return [Players(players) for players in zip_varlen(*players_list_links)]

    async def _get_episodes_names(
        self, page: str, number_of_episodes: int
    ) -> list[str]:
        response = await self.client.get(page)

        if not response.is_success:
            return []

        functions = re.findall(
            r"resetListe\(\); *[\n\r]+\t*(.*?)}",
            response.text,
            re.DOTALL,
        )[-1]
        functions_list = split_and_strip(functions, ";")[:-1]

        def episode_name_range(*args):
            return [f"Episode {n}" for n in range(*args)]

        episodes_name: list[str] = []
        for function in functions_list:
            call_start = function.find("(")
            function, args_sting = function[:call_start], function[call_start + 1 : -1]
            args = literal_eval(args_sting + ",")  # Warning: Can crash

            match function:
                case "creerListe":
                    episodes_name += episode_name_range(int(args[0]), int(args[1]) + 1)
                case "finirListe" | "finirListeOP":
                    episodes_name += episode_name_range(
                        int(args[0]),
                        int(args[0]) + number_of_episodes - len(episodes_name),
                    )
                    break
                case "newSP":
                    episodes_name.append(f"Episode {args[0]}")
                case "newSPF":
                    episodes_name.append(args[0])
                case _:
                    raise NotImplementedError("Please report to the developer")

        return episodes_name

    @staticmethod
    def _extend_episodes(
        current: list[tuple[str, Languages]],
        new: tuple[LANG_ID, list[str], list[Players]],
    ) -> list[tuple[str, Languages]]:
        """
        Extend a list of episodes AKA (name, languages) from a list names and players corresponding to a language
        while preserving the relative order of names.
        This function is intended to be used with reduce.
        """
        lang, names, players_list = new  # Unpack args. This is due to reduce

        fusion = []
        curr_done = 0
        for name_new, players in zip(names, players_list):
            for pos, (name_current, languages) in enumerate(current[curr_done:]):
                if name_new == name_current:
                    languages[lang] = players
                    fusion.extend(current[curr_done : curr_done + pos + 1])
                    curr_done += pos + 1
                    break
            else:
                fusion.append((name_new, Languages({lang: players})))
        fusion.extend(current[curr_done:])
        return fusion

    async def episodes(self) -> list[Episode]:
        players_list = await asyncio.gather(
            *(self._get_players_from(page) for page in self.pages),
        )

        episodes_names = await asyncio.gather(
            *(
                self._get_episodes_names(page, len(episodes_page))
                for page, episodes_page in zip(self.pages, players_list)
            )
        )

        episodes: list[tuple[str, Languages]] = reduce(
            self._extend_episodes, zip(lang_ids, episodes_names, players_list), []
        )

        return [
            Episode(
                languages,
                self.serie_name,
                self.name,
                name,
                index,
            )
            for index, (name, languages) in enumerate(episodes, start=1)
        ]

    def __repr__(self):
        return f"Season({self.name!r}, {self.serie_name!r})"

    def __str__(self):
        return self.name
