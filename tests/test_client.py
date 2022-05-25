import asyncio
import os
import pytest
import tempfile
import json

import cdblib

from onlineconf import Config
from onlineconf.util import get_event_loop


@pytest.fixture
def cdb_writer():
    _, filename = tempfile.mkstemp()
    fp = open(filename, "wb")
    writer = cdblib.Writer(fp)

    yield writer, fp, filename
    os.remove(filename)


@pytest.fixture
def yaml_writer():
    _, cdb_filename = tempfile.mkstemp()
    _, yaml_filename = tempfile.mkstemp()

    yield cdb_filename, yaml_filename
    os.remove(cdb_filename)
    os.remove(yaml_filename)


# @pytest.fixture
# def get_filename():
#     _, filename = tempfile.mkstemp()
#     yield filename
#     os.remove(filename)


# class CDBWriter(object):
#         def __init__(self, filename):
#             self.fp = open(filename, "wb")
#             self.writer = cdblib.Writer(self.fp)
#         def __enter__(self):
#             return self.writer
#         def __exit__(self, type, value, traceback):
#             self.writer.finalize()
#             self.fp.close()

class TestReadConfig:

    def test_read_string_value(self, cdb_writer):
        writer, fp, filename = cdb_writer
        key, value = "/my/service", "123"

        writer.put(key.encode(), f"s{value}".encode())
        writer.finalize()
        fp.close()

        conf = Config.read(filename, reload_interval=None)

        saved_value = conf.get(key)
        assert isinstance(saved_value, str)
        assert saved_value == value

    def test_read_json_value(self, cdb_writer):
        writer, fp, filename = cdb_writer
        key, value = "/my/service", dict(key="value")

        writer.put(key.encode(), f"j{json.dumps(value)}".encode())
        writer.finalize()
        fp.close()

        conf = Config.read(filename, reload_interval=None)

        saved_value = conf.get(key)
        assert isinstance(saved_value, dict)
        assert saved_value == value

    def test_read_json_value_with_unicode(self, cdb_writer):
        writer, fp, filename = cdb_writer
        key, value = "/my/service", dict(key="сьешь еще этих булочек")

        writer.put(key.encode(), f"j{json.dumps(value)}".encode())
        writer.finalize()
        fp.close()

        conf = Config.read(filename, reload_interval=None)

        saved_value = conf.get(key)
        assert isinstance(saved_value, dict)
        assert saved_value == value

    def test_get_items(self, cdb_writer):
        writer, fp, filename = cdb_writer
        items = [
            (b"/my/service/param1", b"value1"),
            (b"/my/service/param2", b"value2"),
            (b"/my/service/param3", b"value3"),
        ]

        for item in items:
            writer.put(*item)
        writer.finalize()
        fp.close()

        conf = Config.read(filename, reload_interval=None)
        saved_items = conf.items()

        assert saved_items == items

    def test_get_keys(self, cdb_writer):
        writer, fp, filename = cdb_writer
        keys = [
            b"/my/service/param1",
            b"/my/service/param2",
            b"/my/service/param3"
        ]

        for key in keys:
            writer.put(key)
        writer.finalize()
        fp.close()

        conf = Config.read(filename, reload_interval=None)
        saved_keys = conf.keys()

        assert saved_keys == keys

    def test_contains(self, cdb_writer):
        writer, fp, filename = cdb_writer
        key = b"/my/service/param1"

        writer.put(key)
        writer.finalize()
        fp.close()

        conf = Config.read(filename, reload_interval=None)
        assert key in conf
        assert b"nonexistent_key" not in conf

    def test_reload(self, cdb_writer):
        writer, fp, filename = cdb_writer
        key, init_value, new_value = "key", "value", "new_value"

        # put init value
        writer.put(key.encode(), f"s{init_value}".encode())
        writer.finalize()
        fp.close()

        loop = get_event_loop()
        conf = Config.read(filename=filename, reload_interval=1, loop=loop)

        # put new value
        with open(filename, "wb") as f:
            writer = cdblib.Writer(f)
            writer.put(key.encode(), f"s{new_value}".encode())
            writer.finalize()

        assert conf.get(key) == init_value

        # wait until config file reloaded
        loop.run_until_complete(asyncio.sleep(conf._reload_interval + 1))

        assert conf.get(key) == new_value

    def test_key_not_found(self, cdb_writer):
        writer, fp, filename = cdb_writer
        writer.finalize()
        fp.close()

        conf = Config.read(filename, reload_interval=None)

        with pytest.raises(KeyError):
            conf.get("/missing_key")


class TestConvertYamlToCdb:
    def test_fill_cdb_with_yaml(self, yaml_writer):
        cdb_filename, yaml_filename = yaml_writer

        _yaml = """
            service:
              db:
                connection:
                  host: localhost
                  port: 5432
                pool_size: 10
              float: 5.35
              unicode: привет
              list: [1, 2, 3, 4, string]"""

        with open(yaml_filename, "w") as f:
            f.write(_yaml)

        conf = Config(cdb_filename)
        conf.fill_from_yaml(yaml_filename)

        cdb_conf = Config.read(cdb_filename, reload_interval=None)

        assert cdb_conf.get("/service/db/connection/host") == "localhost"
        assert cdb_conf.get("/service/db/connection/port") == "5432"
        assert cdb_conf.get("/service/db/pool_size") == "10"
        assert cdb_conf.get("/service/float") == "5.35"
        assert cdb_conf.get("/service/unicode") == "привет"
        assert cdb_conf.get("/service/list") == [1, 2, 3, 4, "string"]
