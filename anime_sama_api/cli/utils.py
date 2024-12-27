import sys
from collections.abc import Callable
from typing import TypeVar

from rich import print

T = TypeVar("T")


def safe_input(
    text: str, transform: Callable[[str], T], exceptions=(ValueError, IndexError)
) -> T:
    while True:
        try:
            print(text, end="")
            output = input()
            return transform(output)
        except exceptions:
            pass


def print_selection(choices: list, print_choices=True) -> None:
    if len(choices) == 0:
        print("[red]No result")
        sys.exit()
    if len(choices) == 1:
        print(f"-> \033[0;34m{choices[0]}")
        return
    if not print_choices:
        return

    for index, choice in enumerate(choices, start=1):
        line_colors = "yellow" if index % 2 == 0 else "white"
        print(
            f"[green][{index:{len(str(len(choices)))}}]",
            f"[{line_colors}]{choice}",
        )


def select_one(choices: list[T], msg="Choose a number", **_) -> T:
    print_selection(choices)
    if len(choices) == 1:
        return choices[0]

    return safe_input(f"{msg}: \033[0;34m", lambda string: choices[int(string) - 1])


def select_range(choices: list[T], msg="Choose a range", print_choices=True) -> list[T]:
    print_selection(choices, print_choices)

    if len(choices) == 1:
        return [choices[0]]

    def transform(string: str) -> list[T]:
        ints_set = set()
        for args in string.split(","):
            ints = [int(num) for num in args.split("-")]

            if len(ints) == 1:
                ints_set.add(ints[0])
            elif len(ints) == 2:
                ints_set.update(range(ints[0], ints[1] + 1))
            else:
                raise ValueError

        return [choices[i - 1] for i in ints_set]

    return safe_input(
        f"{msg} [green][1-{len(choices)}]:[/] \033[0;34m",
        transform,
    )


def keyboard_inter():
    print("\n[red]Exiting...")
    sys.exit()
