import asyncio
from collections.abc import AsyncIterator, Generator, Sequence
from dataclasses import dataclass, field
import logging
import re

from httpx import AsyncClient

from .episode import Episode
from .season import Season
from .langs import Lang, flags
from .utils import filter_literal, is_Literal
from .catalogue import Catalogue, Category


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EpisodeRelease:
    page_url: str
    image_url: str
    serie_name: str
    categories: tuple[Category]
    language: Lang
    descriptive: str

    def get_real_episodes(self) -> list[Episode]:
        raise NotImplementedError

    @property
    def fancy_name(self) -> str:
        return f"{self.serie_name} - {self.descriptive} {flags.get(self.language, '')}"


class AnimeSama:
    def __init__(self, site_url: str, client: AsyncClient | None = None) -> None:
        self.site_url = site_url
        self.client = client or AsyncClient()

    async def _get_homepage_section(self, section_name: str, how_many=1) -> str:
        homepage = await self.client.get(self.site_url)

        if not homepage.is_success:
            return ""

        sections = homepage.text.split("<!--")
        for index, section in enumerate(sections):
            comment_end_pos = section.find("-->")
            if section_name in section[:comment_end_pos]:
                return "<!--" + "<!--".join(sections[index : index + how_many])

        return ""

    def _yield_catalogues_from(self, html: str) -> Generator[Catalogue]:
        text_without_script = re.sub(r"<script[\W\w]+?</script>", "", html)
        for match in re.finditer(
            rf"href=\"({self.site_url}catalogue/.+)\"[\W\w]+?src=\"(.+?)\"[\W\w]+?>(.*)\n?<[\W\w]+?>(.*)\n?<[\W\w]+?>(.*)\n?<[\W\w]+?>(.*)\n?<[\W\w]+?>(.*)\n?<",
            text_without_script,
        ):
            url, image_url, name, alternative_names, genres, categories, languages = (
                match.groups()
            )
            alternative_names = (
                alternative_names.split(", ") if alternative_names else []
            )
            genres = genres.split(", ") if genres else []
            categories = categories.split(", ") if categories else []
            languages = languages.split(", ") if languages else []

            def not_in_literal(value):
                logger.warning(
                    f"Error while parsing '{value}'. \nPlease report this to the developer with URL: {url}"
                )

            categories_checked: set[Category] = set(
                filter_literal(categories, Category, not_in_literal)
            )  # type: ignore
            languages_checked: set[Lang] = set(
                filter_literal(languages, Lang, not_in_literal)
            )  # type: ignore

            yield Catalogue(
                url=url,
                name=name,
                alternative_names=alternative_names,
                genres=genres,
                categories=categories_checked,
                languages=languages_checked,
                image_url=image_url,
                client=self.client,
            )

    def _yield_release_episodes_from(self, html: str) -> Generator[EpisodeRelease]:
        for match in re.finditer(
            rf"href=\"({self.site_url}catalogue/.+?/.+?/)[\W\w]+?src=\"(.+?)\"[\W\w]+?>(.*)\n?<[\W\w]+?>(.*)\n?<[\W\w]+?>(.*)\n?<[\W\w]+?>(.*)\n?<",
            html,
        ):
            (
                season_url,
                image_url,
                serie_name,
                categories,
                language,
                descriptive,
            ) = match.groups()
            categories = categories.split(", ") if categories else ["Anime"]
            language = language.strip()

            def not_in_literal(value):
                logger.warning(
                    f"Error while parsing '{value}'. \nPlease report this to the developer with URL: {season_url} (from homepage)"
                )

            categories_checked: tuple[Category] = tuple(
                filter_literal(categories, Category, not_in_literal)
            )  # type: ignore
            is_Literal(language, Lang, not_in_literal)

            yield EpisodeRelease(
                page_url=season_url,
                image_url=image_url,
                serie_name=serie_name,
                categories=categories_checked,
                language=language,  # type: ignore
                descriptive=descriptive,
            )

    async def search(self, query: str) -> list[Catalogue]:
        response = (
            await self.client.get(f"{self.site_url}catalogue/?search={query}")
        ).raise_for_status()

        pages_regex = re.findall(r"page=(\d+)", response.text)

        if not pages_regex:
            return []

        last_page = int(pages_regex[-1])

        responses = [response] + await asyncio.gather(
            *(
                self.client.get(f"{self.site_url}catalogue/?search={query}&page={num}")
                for num in range(2, last_page + 1)
            )
        )

        catalogues = []
        for response in responses:
            if not response.is_success:
                continue

            catalogues += list(self._yield_catalogues_from(response.text))

        return catalogues

    async def search_iter(self, query: str) -> AsyncIterator[Catalogue]:
        response = (
            await self.client.get(f"{self.site_url}catalogue/?search={query}")
        ).raise_for_status()

        pages_regex = re.findall(r"page=(\d+)", response.text)

        if not pages_regex:
            raise StopAsyncIteration

        last_page = int(pages_regex[-1])

        for catalogue in self._yield_catalogues_from(response.text):
            yield catalogue

        for number in range(2, last_page + 1):
            response = await self.client.get(
                f"{self.site_url}catalogue/?search={query}&page={number}"
            )

            if not response.is_success:
                continue

            for catalogue in self._yield_catalogues_from(response.text):
                yield catalogue

    async def catalogues_iter(self) -> AsyncIterator[Catalogue]:
        async for catalogue in self.search_iter(""):
            yield catalogue

    async def all_catalogues(self) -> list[Catalogue]:
        return await self.search("")

    async def planning(self) -> list[list[Season]]:
        # Get from homepage, return value should be change
        raise NotImplementedError

    async def new_episodes(self) -> list[EpisodeRelease]:
        """
        Return the new available episodes on anime-sama using the homepage sorted from oldest to newest.
        """
        section = await self._get_homepage_section("ajouts animes", 4)
        release_episodes = list(self._yield_release_episodes_from(section))
        return list(reversed(release_episodes))

    """async def new_scans(self) -> list[Scan]:
        raise NotImplementedError"""

    async def new_content(self) -> list[Catalogue]:
        raise NotImplementedError

    async def classics(self) -> list[Catalogue]:
        raise NotImplementedError

    async def highlights(self) -> list[Catalogue]:
        raise NotImplementedError
