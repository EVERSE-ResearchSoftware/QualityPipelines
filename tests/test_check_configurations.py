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


class Foo:
    indicators = ["known", "unconfigured"]

    def known(self, url, branch):
        pass


class Empty:
    indicators = []


class TestCheckConfigurations(unittest.TestCase):
    def test_real_repository_is_consistent(self):
        """The repository's configs and plugins pass the check with no errors."""
        self.assertEqual(mod.check(mod.load_configs(), mod.load_plugins()), [])

    def test_check_reports_missing_keys_and_bad_names(self):
        """Missing keys, unknown plugins and undeclared indicators are reported."""
        configs = [
            (
                "c.json",
                [
                    {"plugin": "Foo"},
                    {"name": "known", "@id": "u"},
                    {"name": "known", "plugin": "Nope", "@id": "u"},
                    {"name": "helper", "plugin": "Foo", "@id": "u"},
                ],
                None,
            )
        ]
        errors = mod.check(configs, {"Foo": Foo})
        reasons = " ".join(error[3] for error in errors)
        self.assertIn("missing key(s): name, @id", reasons)
        self.assertIn("missing key(s): plugin", reasons)
        self.assertIn("plugin is not exported", reasons)
        self.assertIn("not declared", reasons)
        self.assertTrue(any("complete.json" in error[0] for error in errors))

    def test_main_exit_codes(self):
        """main returns 0 on success and 1 when inconsistencies are found."""
        with patch.object(mod, "load_configs", return_value=[]), patch.object(
            mod, "load_plugins", return_value={"Empty": Empty}
        ):
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(mod.main(), 0)
            self.assertIn("OK", out.getvalue())

        with patch.object(mod, "load_configs", return_value=[]), patch.object(
            mod, "load_plugins", return_value={"Foo": Foo}
        ):
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(mod.main(), 1)
            self.assertIn("INCONSISTENCIES", out.getvalue())


if __name__ == "__main__":
    unittest.main()