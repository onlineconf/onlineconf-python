import asyncio
import json
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Tuple, Union

import aiofiles
import cdblib
import yaml

from onlineconf.util import get_event_loop

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop


__all__ = ("Config",)


class Config:
    def __init__(
        self,
        filename: str,
        reload_interval: Optional[int] = None,
        loop: Optional["AbstractEventLoop"] = None,
    ) -> None:
        self._filename = filename
        self._reload_interval = reload_interval
        self._reload_task: Optional[asyncio.Task[None]] = None
        self._loop = loop if loop else get_event_loop()

    @classmethod
    def read(
        cls,
        filename: str,
        reload_interval: Optional[int] = 30,
        loop: Optional["AbstractEventLoop"] = None,
    ) -> "Config":
        """Read a cdb file and schedule periodic reload if needed"""
        _config = cls(filename=filename, reload_interval=reload_interval, loop=loop)

        with open(_config._filename, "rb") as f:
            _config.cdb = cdblib.Reader(f.read())

        if reload_interval:
            _config._reload_task = _config._loop.create_task(_config._schedule_reload())
        return _config

    def get(self, key: str) -> Union[str, Dict[str, Any]]:
        return self._get(key)

    def __getitem__(self, key: str) -> Union[str, Dict[str, Any]]:
        return self._get(key)

    def _get(self, key: str) -> Union[str, Dict[str, Any]]:
        """Get value by key and convert it to corresponding type"""
        binary_value = self.cdb.get(key.encode())
        if binary_value is None:
            raise KeyError(f"Key `{key}` is not found in config")
        return self._cast_value(binary_value)

    def __contains__(self, key: str):
        """Return True if key exists in the config"""
        return key in self.cdb

    def items(self) -> List[Tuple[bytes, bytes]]:
        """Get config (key, value) pairs"""
        return self.cdb.items()

    def keys(self) -> List[bytes]:
        """Get list of config keys"""
        return self.cdb.keys()

    def values(self) -> List[bytes]:
        """Get list of config values"""
        return self.cdb.values()

    async def _schedule_reload(self):
        if self._reload_interval is None:
            raise RuntimeError("'reload_interval' must be defined")

        while True:
            async with aiofiles.open(self._filename, "rb") as f:
                _config = await f.read()
            self.cdb = cdblib.Reader(_config)
            await asyncio.sleep(self._reload_interval)

    def fill_from_yaml(self, filename: str):
        """Read yaml file, convert parameters and save them to cdb file"""
        with open(filename) as f:
            conf = yaml.full_load(f.read())

        cdb_items = self._flatten_dict(conf)

        with open(self._filename, "wb") as f:
            writer = cdblib.Writer(f)
            for k, v in cdb_items:
                writer.put(k.encode(), v.encode())
            writer.finalize()

    async def shutdown(self):
        if self._reload_task:
            self._reload_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._reload_task

    @staticmethod
    def _cast_value(value: bytes) -> Union[str, Dict[str, Any]]:
        # Decode bytes to unicode
        value_decode = value.decode()
        prefix = value_decode[:1]
        value_decode = value_decode[1:]

        if prefix == "s":
            return value_decode
        elif prefix == "j":
            return json.loads(value_decode)
        else:
            raise ValueError

    def _flatten_dict(
        self, d: Dict[str, Any], path: str = ""
    ) -> Iterator[Tuple[str, str]]:
        """Return dict items as tuples: (xpath-like key, value)"""
        for key, value in d.items():
            _path = "/".join((path, key))
            if isinstance(value, dict):
                yield from self._flatten_dict(value, _path)
            elif isinstance(value, list):
                yield _path, f"j{json.dumps(value)}"
            else:
                try:
                    json.loads(value)
                except (TypeError, json.decoder.JSONDecodeError):
                    yield _path, f"s{value}"
                else:
                    yield _path, f"j{value}"
