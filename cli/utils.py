import sys
from collections.abc import Callable
from typing import Literal, TypeVar

from termcolor import colored, RESET, COLORS


T = TypeVar("T")

Color = Literal[
    "black",
    "grey",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "light_grey",
    "dark_grey",
    "light_red",
    "light_green",
    "light_yellow",
    "light_blue",
    "light_magenta",
    "light_cyan",
    "white",
]


def put_color(color: Color):
    return f"\033[{COLORS[color]}m"


def safe_input(
    text: str, transform: Callable[[str], T], exceptions=(ValueError, IndexError)
) -> T:
    while True:
        try:
            output = input(text)
            print(RESET, end="")
            return transform(output)
        except exceptions:
            pass


def print_selection(choices: list, print_choices=True) -> None:
    if len(choices) == 0:
        sys.exit(colored("No result", "red"))
    if len(choices) == 1:
        print(f"-> {colored(choices[0], 'blue')}")
        return
    if not print_choices:
        return

    for index, choice in enumerate(choices, start=1):
        line_colors: Color = "yellow" if index % 2 == 0 else "white"
        print(
            colored(f"[{index:{len(str(len(choices)))}}]", "green"),
            colored(choice, line_colors),
        )


def select_one(choices: list[T], msg="Choose a number", **_) -> T:
    print_selection(choices)
    if len(choices) == 1:
        return choices[0]

    return safe_input(
        f"{msg}: " + put_color("blue"), lambda string: choices[int(string) - 1]
    )


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
        f"{msg} {colored(f'[1-{len(choices)}]', 'green')}: {put_color('blue')}",
        transform,
    )


def keyboard_inter():
    print(colored("\nExiting...", "red"))
    sys.exit()
