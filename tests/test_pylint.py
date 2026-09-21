import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from resqui.core import Context
from resqui.plugins.pylint import Pylint


def _fake_run_factory(message_type_count):
    """Builds a side_effect that simulates git clone/checkout + pylint json2."""
    def fake_run(args, **kwargs):
        cmd = args[0] if isinstance(args, list) else args
        # git clone (last argument is the destination path)
        if cmd == "git" and args[1] == "clone":
            dest = args[-1]
            os.makedirs(dest, exist_ok=True)
            Path(dest, "lib.py").write_text("x = 1\n")
            return SimpleNamespace(stdout="", stderr="")
        # git checkout / any other git call
        if cmd == "git":
            return SimpleNamespace(stdout="", stderr="")
        # pylint
        return SimpleNamespace(
            stdout=json.dumps({"statistics": {"messageTypeCount": message_type_count}}),
            stderr="",
            returncode=0,
        )
    return fake_run


class TestPylintPlugin(unittest.TestCase):

    def _make_plugin(self):
        plugin = Pylint.__new__(Pylint)
        plugin.context = Context(github_token="token")
        plugin.executor = SimpleNamespace(temp_dir="/tmp/fake-venv")
        plugin._cache = {}
        return plugin

    def test_code_smells_ok_false(self):
        """1 code smell over 1 LOC exceeds the 50 per 1000 LOC threshold."""
        counts = {"refactor": 1, "convention": 0, "warning": 0, "error": 0, "fatal": 0, "info": 0}
        plugin = self._make_plugin()
        with tempfile.TemporaryDirectory() as tmp:
            fake_run = _fake_run_factory(counts)
            with patch("resqui.plugins.pylint.create_workspace") as mock_ws:
                mock_ws.return_value.__enter__ = lambda s: s
                mock_ws.return_value.__exit__ = MagicMock(return_value=False)
                mock_ws.return_value.local_path = tmp
                with patch("resqui.plugins.pylint.subprocess.run", side_effect=fake_run):
                    result = plugin.code_smells_ok("https://github.com/example/repo", "main")

        self.assertEqual(result.output, "false")
        self.assertFalse(result.success)
        self.assertIn("1 code smells", result.evidence)


    def test_code_smells_ok_true(self):
        """Low code smell ratio stays under the 50/1000 LOC threshold."""
        counts = {"refactor": 0, "convention": 0, "warning": 0, "error": 0, "fatal": 0, "info": 0}
        plugin = self._make_plugin()
        with tempfile.TemporaryDirectory() as tmp:
            fake_run = _fake_run_factory(counts)
            with patch("resqui.plugins.pylint.create_workspace") as mock_ws:
                mock_ws.return_value.__enter__ = lambda s: s
                mock_ws.return_value.__exit__ = MagicMock(return_value=False)
                mock_ws.return_value.local_path = tmp
                with patch("resqui.plugins.pylint.subprocess.run", side_effect=fake_run):
                    result = plugin.code_smells_ok("https://github.com/example/repo", "main")

        self.assertEqual(result.output, "true")
        self.assertTrue(result.success)


    def test_low_python_ratio_skippable(self):
        """Repository with less than 20% Python files,handle_skip."""
        def fake_run_no_python(args, **kwargs):
            if args[0] == "git" and args[1] == "clone":
                dest = args[-1]
                os.makedirs(dest, exist_ok=True)
                Path(dest, "lib.txt").write_text("x = 1\n")
                return SimpleNamespace(stdout="", stderr="")
            return SimpleNamespace(stdout="", stderr="")

        plugin = self._make_plugin()
        with tempfile.TemporaryDirectory() as tmp:
            with patch("resqui.plugins.pylint.create_workspace") as mock_ws:
                mock_ws.return_value.__enter__ = lambda s: s
                mock_ws.return_value.__exit__ = MagicMock(return_value=False)
                mock_ws.return_value.local_path = tmp
                with patch("resqui.plugins.pylint.subprocess.run", side_effect=fake_run_no_python):
                    result = plugin.code_smells_ok("https://github.com/example/repo", "main")

        self.assertEqual(result.output, "indeterminate")
        self.assertTrue(result.success)