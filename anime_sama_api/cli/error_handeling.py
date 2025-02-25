from logging import LogRecord
from typing import Literal

Reaction = Literal["continue", "retry", "crash", ""]

how_to_react: dict[Reaction, tuple[str, ...]] = {
    "continue": (
        "[Errno 61] Connection refused",
        "Remote end closed connection without response",
    ),
    "retry": ("The read operation timed out",),
    "crash": (),
}


def reaction_to(msg: str) -> Reaction:
    for reaction, error_msgs in how_to_react.items():
        for error_msg in error_msgs:
            if error_msg in msg:
                return reaction
    return ""


def is_error_handle(msg: str):
    return bool(reaction_to(msg))


def YDL_log_filter(record: LogRecord):
    if record.filename != "YoutubeDL.py":
        return True

    match record.levelname:
        case "WARNING":
            if "Falling back on generic information extractor" in record.msg:
                return False
        case "ERROR":
            return not is_error_handle(record.msg)
        case _:
            return True
