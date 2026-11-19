import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from resqui.core import Context
from resqui.plugins.interrogate import Interrogate


def _fake_run_factory(write_file="mod.py", content="def f():\n    pass\n"):
    """Simulates git clone + checkout, writing one .py file into the
    cloned repo so the plugin's 'no_python' short-circuit isn't triggered."""
    def fake_run(args, **kwargs):
        cmd = args[0] if isinstance(args, list) else args
        if cmd == "git" and args[1] == "clone":
            dest = args[-1]
            os.makedirs(dest, exist_ok=True)
            (Path(dest) / write_file).write_text(content)
            return SimpleNamespace(stdout="", stderr="")
        if cmd == "git":
            return SimpleNamespace(stdout="", stderr="")
        raise AssertionError(f"unexpected subprocess call: {args}")
    return fake_run


def _fake_execute_result(percentage, total=10):
    covered = int(total * percentage / 100)
    return SimpleNamespace(
        returncode=0,
        stdout=json.dumps({
            "total": total,
            "covered": covered,
            "missing": total - covered,
            "percentage": percentage,
        }),
        stderr="",
    )


class TestInterrogatePlugin(unittest.TestCase):

    def _make_plugin(self):
        plugin = Interrogate.__new__(Interrogate)
        plugin.context = Context(github_token="token")
        plugin.executor = MagicMock()
        plugin._cache = {}
        return plugin

    def test_documentation_coverage_ok(self):
        """Coverage at or above 80% passes."""
        plugin = self._make_plugin()
        plugin.executor.execute.return_value = _fake_execute_result(90.0)
        with tempfile.TemporaryDirectory() as tmp:
            with patch("resqui.plugins.interrogate.create_workspace") as mock_ws:
                mock_ws.return_value.__enter__ = lambda s: s
                mock_ws.return_value.__exit__ = MagicMock(return_value=False)
                mock_ws.return_value.local_path = tmp
                with patch("resqui.plugins.interrogate.subprocess.run", side_effect=_fake_run_factory()):
                    result = plugin.code_documentation_coverage_ok("https://github.com/example/repo", "main")

        self.assertEqual(result.output, "true")
        self.assertTrue(result.success)

    def test_documentation_coverage_not_ok(self):
        """Coverage below 80% fails."""
        plugin = self._make_plugin()
        plugin.executor.execute.return_value = _fake_execute_result(10.0)
        with tempfile.TemporaryDirectory() as tmp:
            with patch("resqui.plugins.interrogate.create_workspace") as mock_ws:
                mock_ws.return_value.__enter__ = lambda s: s
                mock_ws.return_value.__exit__ = MagicMock(return_value=False)
                mock_ws.return_value.local_path = tmp
                with patch("resqui.plugins.interrogate.subprocess.run", side_effect=_fake_run_factory()):
                    result = plugin.code_documentation_coverage_ok("https://github.com/example/repo", "main")

        self.assertEqual(result.output, "false")
        self.assertFalse(result.success)

    def test_syntax_error_reports_culprit(self):
        """A repo with an unparsable .py file (e.g. unresolved merge
        markers) yields 'indeterminate' and names the offending file. Example with fairos when it was checked"""
        plugin = self._make_plugin()
        plugin.executor.execute.return_value = SimpleNamespace(
            returncode=1, stdout="", stderr="Traceback (most recent call last): ...",
        )
        broken = "<<<<<<<< HEAD\ndef f():\n    pass\n========\n>>>>>>>> dev\n"
        with tempfile.TemporaryDirectory() as tmp:
            with patch("resqui.plugins.interrogate.create_workspace") as mock_ws:
                mock_ws.return_value.__enter__ = lambda s: s
                mock_ws.return_value.__exit__ = MagicMock(return_value=False)
                mock_ws.return_value.local_path = tmp
                with patch(
                    "resqui.plugins.interrogate.subprocess.run",
                    side_effect=_fake_run_factory(write_file="broken.py", content=broken),
                ):
                    result = plugin.code_documentation_coverage_ok("https://github.com/example/repo", "main")

        self.assertEqual(result.output, "indeterminate")
        self.assertIn("broken.py", result.evidence)