import asyncio
import os
import unittest
import tempfile
import json

import cdblib
import yaml

from onlineconf import Config


class ReadConfig(unittest.TestCase):
    cdb_writer = cdblib.Writer

    def setUp(self):
        _, self.cdb_filename = tempfile.mkstemp()
        self.fp = open(self.cdb_filename, 'wb')
        self.writer = self.cdb_writer(self.fp)

    def tearDown(self):
        self.fp.close()
        os.remove(self.cdb_filename)

    def finalize_cdb(self):
        self.writer.finalize()
        self.fp.close()

    def test_read_string_value(self):
        key, value = '/my/service', '123'

        self.writer.put(key, f's{value}')
        self.finalize_cdb()

        conf = Config.read(self.cdb_filename, reload=False)

        saved_value = conf.get(key)
        self.assertIsInstance(saved_value, str)
        self.assertEqual(saved_value, value)

    def test_read_json_value(self):
        key, value = '/my/service', dict(key='value')

        self.writer.put(key, f'j{json.dumps(value)}')
        self.finalize_cdb()

        conf = Config.read(self.cdb_filename, reload=False)

        saved_value = conf.get(key)
        self.assertIsInstance(saved_value, dict)
        self.assertEqual(saved_value, value)

    def test_get_items(self):
        items = [
            ('/my/service/param1', 'value1'),
            ('/my/service/param2', 'value2'),
            ('/my/service/param3', 'value3'),
        ]

        for item in items:
            self.writer.put(*item)
        self.finalize_cdb()

        conf = Config.read(self.cdb_filename, reload=False)
        saved_items = conf.items()

        self.assertEqual(saved_items, [tuple(map(str.encode, item)) for item in items])

    def test_get_keys(self):
        keys = [
            '/my/service/param1',
            '/my/service/param2',
            '/my/service/param3'
        ]

        for key in keys:
            self.writer.put(key)
        self.finalize_cdb()

        conf = Config.read(self.cdb_filename, reload=False)
        saved_keys = conf.keys()

        self.assertEqual(saved_keys, [key.encode() for key in keys])

    def test_contains(self):
        key = '/my/service/param1'

        self.writer.put(key)
        self.finalize_cdb()

        conf = Config.read(self.cdb_filename, reload=False)
        self.assertIn(key, conf)
        self.assertNotIn('nonexistent_key', conf)

    def test_reload(self):
        key, init_value, new_value = 'key', 'value', 'new_value'

        # put init value
        self.writer.put(key, f's{init_value}')
        self.finalize_cdb()

        conf = Config.read(self.cdb_filename, reload_interval=1)

        # put new value
        with open(self.cdb_filename, 'wb') as f:
            writer = self.cdb_writer(f)
            writer.put(key, f's{new_value}')
            writer.finalize()

        self.assertEqual(conf.get(key), init_value)

        loop = asyncio.get_event_loop()
        # wait until config file reloaded
        loop.run_until_complete(asyncio.sleep(conf._reload_interval + 1))

        self.assertEqual(conf.get(key), new_value)


class ConvertYamlToCdb(unittest.TestCase):
    cdb_writer = cdblib.Writer

    def setUp(self):
        _, self.cdb_filename = tempfile.mkstemp()
        _, self.yaml_filename = tempfile.mkstemp()

    def tearDown(self):
        os.remove(self.cdb_filename)
        os.remove(self.yaml_filename)

    def test_fill_cdb_with_yaml(self):
        conf = {
            'service': {
                'db': {
                    'connection': {
                        'host': 'localhost',
                        'port': 5432
                    },
                    'pool_size': 10
                },
                'float': 5.35
            }
        }

        with open(self.yaml_filename, 'w') as f:
            f.write(yaml.dump(conf))

        conf = Config(self.cdb_filename)
        conf.fill_from_yaml(self.yaml_filename)

        cdb_conf = Config.read(self.cdb_filename, reload=False)

        self.assertEqual(cdb_conf.get('/service/db/connection/host'), 'localhost')
        self.assertEqual(cdb_conf.get('/service/db/connection/port'), '5432')
        self.assertEqual(cdb_conf.get('/service/db/pool_size'), '10')
        self.assertEqual(cdb_conf.get('/service/float'), '5.35')


if __name__ == '__main__':
    unittest.main()
