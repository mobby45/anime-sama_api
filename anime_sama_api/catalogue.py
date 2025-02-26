import re

from httpx import AsyncClient

from .season import Season


class Catalogue:
    def __init__(self, url: str, name="", client: AsyncClient | None = None) -> None:
        self.url = url + "/" if url[-1] != "/" else url
        self.name = name or url.split("/")[-2]
        self.site_url = "/".join(url.split("/")[:3]) + "/"
        self.client = client or AsyncClient()
        self._page = None

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
        seasons = re.findall(
            r'panneauAnime\("(.+?)", *"(.+?)(?:vostfr|vf)"\);', await self.page()
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

    async def correspondance(self):
        search = re.findall(r"Correspondance.+?>(.+?)<", await self.page())

        if not search:
            return ""

        return search[0]

    def __repr__(self):
        return f"Catalogue({self.url!r}, {self.name!r})"

    def __str__(self):
        return self.name

    def __eq__(self, value):
        return self.url == value.url
