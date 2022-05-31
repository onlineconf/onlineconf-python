import asyncio
import json
import os
import tempfile
import unittest

import cdblib

from onlineconf import Config


class ReadConfig(unittest.IsolatedAsyncioTestCase):
    cdb_writer = cdblib.Writer

    def setUp(self):
        _, self.cdb_filename = tempfile.mkstemp()
        self.fp = open(self.cdb_filename, "wb")
        self.writer = self.cdb_writer(self.fp)

    def tearDown(self):
        self.fp.close()
        os.remove(self.cdb_filename)

    def finalize_cdb(self):
        self.writer.finalize()
        self.fp.close()

    async def test_read_string_value(self):
        key, value = "/my/service", "123"

        self.writer.put(key.encode(), f"s{value}".encode())
        self.finalize_cdb()

        conf = await Config.read(self.cdb_filename, reload_interval=None)

        saved_value = conf.get(key)
        self.assertIsInstance(saved_value, str)
        self.assertEqual(saved_value, value)

    async def test_read_json_value(self):
        key, value = "/my/service", dict(key="value")

        self.writer.put(key.encode(), f"j{json.dumps(value)}".encode())
        self.finalize_cdb()

        conf = await Config.read(self.cdb_filename, reload_interval=None)

        saved_value = conf.get(key)
        self.assertIsInstance(saved_value, dict)
        self.assertEqual(saved_value, value)

    async def test_read_json_value_with_unicode(self):
        key, value = "/my/service", dict(key="сьешь еще этих булочек")

        self.writer.put(key.encode(), f"j{json.dumps(value)}".encode())
        self.finalize_cdb()

        conf = await Config.read(self.cdb_filename, reload_interval=None)

        saved_value = conf.get(key)
        self.assertIsInstance(saved_value, dict)
        self.assertEqual(saved_value, value)

    async def test_get_items(self):
        items = [
            (b"/my/service/param1", b"value1"),
            (b"/my/service/param2", b"value2"),
            (b"/my/service/param3", b"value3"),
        ]

        for item in items:
            self.writer.put(*item)
        self.finalize_cdb()

        conf = await Config.read(self.cdb_filename, reload_interval=None)
        saved_items = conf.items()

        self.assertEqual(saved_items, items)

    async def test_get_keys(self):
        keys = [b"/my/service/param1", b"/my/service/param2", b"/my/service/param3"]

        for key in keys:
            self.writer.put(key)
        self.finalize_cdb()

        conf = await Config.read(self.cdb_filename, reload_interval=None)
        saved_keys = conf.keys()

        self.assertEqual(saved_keys, keys)

    async def test_contains(self):
        key = b"/my/service/param1"

        self.writer.put(key)
        self.finalize_cdb()

        conf = await Config.read(self.cdb_filename, reload_interval=None)
        self.assertIn(key, conf)  # type: ignore
        self.assertNotIn(b"nonexistent_key", conf)  # type: ignore

    async def test_reload(self):
        key, init_value, new_value = "key", "value", "new_value"

        # put init value
        self.writer.put(key.encode(), f"s{init_value}".encode())
        self.finalize_cdb()

        conf = await Config.read(filename=self.cdb_filename, reload_interval=1)

        # put new value
        with open(self.cdb_filename, "wb") as f:
            writer = self.cdb_writer(f)
            writer.put(key.encode(), f"s{new_value}".encode())
            writer.finalize()

        self.assertEqual(conf.get(key), init_value)

        # wait until config file reloaded
        if conf._reload_interval:
            await asyncio.sleep(conf._reload_interval + 1)
        await conf.shutdown()

        self.assertEqual(conf.get(key), new_value)

    async def test_key_not_found(self):
        self.finalize_cdb()

        conf = await Config.read(self.cdb_filename, reload_interval=None)

        with self.assertRaises(KeyError):
            conf.get("/missing_key")


class ConvertYamlToCdb(unittest.IsolatedAsyncioTestCase):
    cdb_writer = cdblib.Writer

    def setUp(self):
        _, self.cdb_filename = tempfile.mkstemp()
        _, self.yaml_filename = tempfile.mkstemp()

    def tearDown(self):
        os.remove(self.cdb_filename)
        os.remove(self.yaml_filename)

    async def test_fill_cdb_with_yaml(self):
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

        with open(self.yaml_filename, "w") as f:
            f.write(_yaml)

        conf = Config(self.cdb_filename)
        conf.fill_from_yaml(self.yaml_filename)

        cdb_conf = await Config.read(self.cdb_filename, reload_interval=None)

        self.assertEqual(cdb_conf.get("/service/db/connection/host"), "localhost")
        self.assertEqual(cdb_conf.get("/service/db/connection/port"), "5432")
        self.assertEqual(cdb_conf.get("/service/db/pool_size"), "10")
        self.assertEqual(cdb_conf.get("/service/float"), "5.35")
        self.assertEqual(cdb_conf.get("/service/unicode"), "привет")
        self.assertEqual(cdb_conf.get("/service/list"), [1, 2, 3, 4, "string"])


if __name__ == "__main__":
    unittest.main()
