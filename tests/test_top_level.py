import pytest

from anime_sama_api.top_level import AnimeSama
from .data import catalogue_data

pytest_plugins = ("pytest_asyncio",)
anime_sama = AnimeSama(site_url="https://anime-sama.fr/")


@pytest.mark.asyncio
async def test_search():
    assert catalogue_data.one_piece in await anime_sama.search("one piece")
    assert catalogue_data.mha in await anime_sama.search("mha")
    assert catalogue_data.gumball in await anime_sama.search("gumball")


@pytest.mark.asyncio
@pytest.mark.skip(reason="Not Implemented Yet")
async def test_all_catalogues():
    catalogues = await anime_sama.all_catalogues()
    assert catalogue_data.one_piece in catalogues
    assert catalogue_data.mha in catalogues
    assert catalogue_data.gumball in catalogues
