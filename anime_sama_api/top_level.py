import asyncio
from collections.abc import AsyncIterator, Generator
import re

from httpx import AsyncClient

from .catalogue import Catalogue


class AnimeSama:
    def __init__(self, site_url: str, client: AsyncClient | None = None) -> None:
        self.site_url = site_url
        self.client = client or AsyncClient()

    async def search(self, query: str) -> list[Catalogue]:
        response = await self.client.post(
            f"{self.site_url}template-php/defaut/fetch.php", data={"query": query}
        )

        if not response.is_success:
            return []

        links = re.findall(r'href="(.+?)"', response.text)
        names = re.findall(r">(.+?)<\/h3>", response.text)

        return [
            Catalogue(url=link, name=name, client=self.client)
            for link, name in zip(links, names)
        ]

    def _yield_catalogues_from(self, html: str) -> Generator[Catalogue]:
        text_without_script = re.sub(r"<script[\W\w]+?</script>", "", html)
        for url, name in re.findall(
            rf"href=\"({self.site_url}catalogue/.+)\"[\W\w]+?>(.+)</h1>",
            text_without_script,
        ):
            yield Catalogue(
                url,
                name,
                self.client,
            )

    async def catalogues_iter(self) -> AsyncIterator[Catalogue]:
        response = await self.client.get(f"{self.site_url}catalogue/")

        if not response.is_success:
            raise StopAsyncIteration

        available_pages_numbers = [
            int(num) for num in re.findall(r"\?page=(\d+)", response.text)
        ]

        for catalogue in self._yield_catalogues_from(response.text):
            yield catalogue

        for number in range(2, max(available_pages_numbers) + 1):
            response = await self.client.get(f"{self.site_url}catalogue/?page={number}")

            if not response.is_success:
                continue

            for catalogue in self._yield_catalogues_from(response.text):
                yield catalogue

    async def all_catalogues(self) -> list[Catalogue]:
        response = await self.client.get(f"{self.site_url}catalogue/")

        if not response.is_success:
            return []

        available_pages_numbers = [
            int(num) for num in re.findall(r"\?page=(\d+)", response.text)
        ]

        responses = [response] + await asyncio.gather(
            *(
                self.client.get(f"{self.site_url}catalogue/?page={num}")
                for num in range(2, max(available_pages_numbers) + 1)
            )
        )

        catalogues = []
        for response in responses:
            if not response.is_success:
                continue

            catalogues += list(self._yield_catalogues_from(response.text))

        return catalogues
