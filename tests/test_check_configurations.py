import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_configurations.py"
spec = importlib.util.spec_from_file_location("check_configurations", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestCheckConfigurations(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "configurations").mkdir()
        (self.root / "src" / "resqui" / "plugins").mkdir(parents=True)
        for name, value in (
            ("ROOT", self.root),
            ("CONFIG_DIR", self.root / "configurations"),
            ("PLUGINS_DIR", self.root / "src" / "resqui" / "plugins"),
            ("CONFIG_PY", self.root / "src" / "resqui" / "config.py"),
        ):
            patcher = patch.object(mod, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def fixture(self, declared=("known",), entries=None):
        declared = list(declared)
        if entries is None:
            entries = [
                {"name": n, "plugin": "Foo", "@id": "https://example.org/" + n}
                for n in declared
            ]
        plugins = self.root / "src" / "resqui" / "plugins"
        body = "class Foo:\n    indicators = %r\n" % declared
        for name in declared:
            body += "    def %s(self, url, branch):\n        pass\n" % name
        (plugins / "foo.py").write_text(body, encoding="utf-8")
        (plugins / "__init__.py").write_text(
            "from resqui.plugins.foo import Foo\n", encoding="utf-8"
        )
        (self.root / "configurations" / "basic.json").write_text(
            json.dumps({"indicators": entries}), encoding="utf-8"
        )
        (self.root / "src" / "resqui" / "config.py").write_text(
            "DEFAULT_CONFIG = {'indicators': []}\n", encoding="utf-8"
        )

    def test_loaders_find_plugin_and_configs(self):
        self.fixture()
        plugins = mod.load_plugins()
        self.assertEqual(plugins["Foo"]["declared"], ["known"])
        labels = [label for label, _, _ in mod.load_configs()]
        self.assertEqual(
            labels,
            ["configurations/basic.json", "src/resqui/config.py::DEFAULT_CONFIG"],
        )

    def test_check_detects_bad_plugin_and_unconfigured_indicator(self):
        self.fixture(
            entries=[{"name": "known", "plugin": "Nope", "@id": "https://example.org/known"}]
        )
        errors = mod.check(mod.load_configs(), mod.load_plugins())
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("plugin does not exist" in e[3] for e in errors))
        self.assertTrue(any(e[0] == "(no config)" for e in errors))

    def test_check_passes_when_consistent(self):
        self.fixture()
        self.assertEqual(mod.check(mod.load_configs(), mod.load_plugins()), [])

    def test_main_exit_codes(self):
        self.fixture()
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(mod.main(), 0)
        self.assertIn("OK", out.getvalue())

        self.fixture(
            entries=[{"name": "known", "plugin": "Nope", "@id": "https://example.org/known"}]
        )
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(mod.main(), 1)
        self.assertIn("INCONSISTENCIES", out.getvalue())


if __name__ == "__main__":
    unittest.main()