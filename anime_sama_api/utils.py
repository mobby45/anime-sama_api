from typing import TypeVar
from itertools import zip_longest
from collections.abc import Iterable

T = TypeVar("T")


# By Mike Müller (https://stackoverflow.com/a/38059462)
def zip_varlen(*iterables: list[Iterable[T]], sentinel=object()) -> list[list[T]]:
    return [
        [entry for entry in iterable if entry is not sentinel]
        for iterable in zip_longest(*iterables, fillvalue=sentinel)
    ]


def split_and_strip(string: str, delimiter: str) -> list[str]:
    return [part.strip() for part in string.split(delimiter)]
