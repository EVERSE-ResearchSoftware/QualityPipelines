import json
import tempfile
import unittest
from unittest.mock import patch
import io  # noqa: F401

from resqui.config import Configuration, DEFAULT_CONFIG


class TestConfigurationDefaults(unittest.TestCase):
    def test_loads_default_config_when_no_filepath(self):
        with patch("builtins.print"):
            cfg = Configuration()
        self.assertEqual(cfg._cfg, DEFAULT_CONFIG)

    def test_default_config_has_indicators(self):
        with patch("builtins.print"):
            cfg = Configuration()
        self.assertIn("indicators", cfg._cfg)
        self.assertIsInstance(cfg._cfg["indicators"], list)
        self.assertGreater(len(cfg._cfg["indicators"]), 0)

    def test_default_config_indicator_has_required_keys(self):
        with patch("builtins.print"):
            cfg = Configuration()
        for indicator in cfg._cfg["indicators"]:
            with self.subTest(indicator=indicator.get("name")):
                self.assertIn("name", indicator)
                self.assertIn("plugin", indicator)
                self.assertIn("@id", indicator)


class TestConfigurationFromFile(unittest.TestCase):
    def _write_config(self, data):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            return f.name

    def test_loads_from_file(self):
        custom = {"indicators": [{"name": "has_license", "plugin": "X", "@id": "y"}]}
        path = self._write_config(custom)
        with patch("builtins.print"):
            cfg = Configuration(filepath=path)
        self.assertEqual(cfg._cfg, custom)

    def test_file_overrides_defaults(self):
        custom = {"indicators": []}
        path = self._write_config(custom)
        with patch("builtins.print"):
            cfg = Configuration(filepath=path)
        self.assertEqual(cfg._cfg["indicators"], [])
