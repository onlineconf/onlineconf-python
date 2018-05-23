import asyncio
import json
from typing import Union, List, Tuple

import aiofiles as aiofiles
import cdblib

__all__ = ('Config',)


class Config:

    def __init__(self, filename: str, reload_interval=30, loop=None):
        self._filename = filename
        self._reload_interval = reload_interval
        self._loop = loop if loop else asyncio.get_event_loop()

    @classmethod
    def read(cls, filename: str, reload: bool = True, reload_interval: int = None):
        """Read a cdb file and schedule periodic reload if needed"""
        _config = cls(filename, reload_interval)

        with open(_config._filename, 'rb') as f:
            _config.cdb = cdblib.Reader(f.read())

        if reload:
            _config._loop.create_task(_config._schedule_reload())
        return _config

    def get(self, key: str) -> Union[str, dict]:
        return self._get(key)

    def __getitem__(self, key: str) -> Union[str, dict]:
        return self._get(key)

    def _get(self, key: str) -> Union[str, dict]:
        """Get value by key and convert it to corresponding type"""
        binary_value = self.cdb.get(key)
        return self._cast_value(binary_value)

    def __contains__(self, key):
        """Return True if key exists in the config"""
        return self.cdb.has_key(key)

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
        while True:
            async with aiofiles.open(self._filename, 'rb') as f:
                _config = await f.read()
            self.cdb = cdblib.Reader(_config)
            await asyncio.sleep(self._reload_interval)

    @staticmethod
    def _cast_value(value: str) -> Union[str, dict]:
        # Decode bytes to unicode
        value = value.decode()
        prefix = value[:1]
        value = value[1:]

        if prefix == 's':
            return value
        elif prefix == 'j':
            return json.loads(value)
        else:
            raise ValueError