import re

from httpx import AsyncClient

from anime_sama_api.utils import remove_some_js_comments

from .season import Season


class Catalogue:
    def __init__(self, url: str, name="", client: AsyncClient | None = None) -> None:
        self.url = url + "/" if url[-1] != "/" else url
        self.site_url = "/".join(url.split("/")[:3]) + "/"
        self.client = client or AsyncClient()
        self._page = None

        self.name = name or url.split("/")[-2]
        # TODO: Synopsis, genres. Lang?
        # Need async post init

    async def page(self) -> str:
        if self._page is not None:
            return self._page

        response = await self.client.get(self.url)

        if not response.is_success:
            self._page = ""
        else:
            self._page = response.text

        return self._page

    async def seasons(self) -> list[Season]:
        page_without_comments = remove_some_js_comments(string=await self.page())

        seasons = re.findall(
            r'panneauAnime\("(.+?)", *"(.+?)(?:vostfr|vf)"\);', page_without_comments
        )

        seasons = [
            Season(
                url=self.url + link,
                name=name,
                serie_name=self.name,
                client=self.client,
            )
            for name, link in seasons
        ]

        return seasons

    async def advancement(self) -> str:
        search = re.findall(r"Avancement.+?>(.+?)<", await self.page())

        if not search:
            return ""

        return search[0]

    async def correspondence(self) -> str:
        search = re.findall(r"Correspondance.+?>(.+?)<", await self.page())

        if not search:
            return ""

        return search[0]

    async def is_anime(self) -> bool:
        raise NotImplementedError

    async def is_manga(self) -> bool:
        raise NotImplementedError

    async def is_film(self) -> bool:
        raise NotImplementedError

    async def is_other(self) -> bool:
        raise NotImplementedError

    async def alternative_names(self) -> list[str]:
        raise NotImplementedError

    def __repr__(self):
        return f"Catalogue({self.url!r}, {self.name!r})"

    def __str__(self):
        return self.name

    def __eq__(self, value):
        return self.url == value.url
