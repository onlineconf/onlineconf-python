import asyncio
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

__all__ = ("get_event_loop",)

def get_event_loop() -> "AbstractEventLoop":
    if sys.version_info < (3,7):
        return asyncio.get_event_loop()
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    return loop
