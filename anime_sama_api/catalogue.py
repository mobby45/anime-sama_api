import re
from functools import cache

from httpx import AsyncClient

from .season import Season


class Catalogue:
    def __init__(self, url: str, name="", client: AsyncClient | None = None) -> None:
        self.url = url + "/" if url[-1] != "/" else url
        self.name = name or url.split("/")[-2]
        self.site_url = "/".join(url.split("/")[:3]) + "/"
        self.client = client or AsyncClient()

    @cache
    async def page(self) -> str | None:
        response = await self.client.get(self.url)

        if not response.is_success:
            return None

        return response.text

    async def seasons(self) -> list[Season]:
        seasons = re.findall(
            r'panneauAnime\("(.+?)", *"(.+?)(?:vostfr|vf)"\);', await self.page() or ""
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
        search = re.search(r"Avancement.+?>(.+?)<", await self.page() or "")

        if search is None:
            return ""

        return search.group(0)

    async def correspondance(self):
        search = re.search(r"Correspondance.+?>(.+?)<", await self.page() or "")

        if search is None:
            return ""

        return search.group(0)

    def __repr__(self):
        return f"Catalogue({self.url!r}, {self.name!r})"

    def __str__(self):
        return self.name
