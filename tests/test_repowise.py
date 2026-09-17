import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from resqui.core import Context
from resqui.plugins.repowise import Repowise


def _fake_run_factory(targets):
    """Builds a side_effect that simulates git clone/rev-list + repowise risk."""
    def fake_run(args, **kwargs):
        cmd = args[0] if isinstance(args, list) else args
        # git clone
        if cmd == "git" and args[1] == "clone":
            dest = args[3]
            os.makedirs(dest, exist_ok=True)
            # create .git so that rev-list works
            os.makedirs(os.path.join(dest, ".git"), exist_ok=True)
            Path(dest, "lib.py").write_text("x = 1\n")
            return SimpleNamespace(stdout="", stderr="")
        # git checkout / git rev-list
        if cmd == "git":
            return SimpleNamespace(stdout="10\n", stderr="")
        # repowise init
        if "init" in args:
            return SimpleNamespace(stdout="", stderr="")
        # repowise risk
        if "risk" in args:
            return SimpleNamespace(
                stdout=json.dumps({"targets": targets}),
                stderr=""
            )
        return SimpleNamespace(stdout="", stderr="")
    return fake_run


class TestRepowisePlugin(unittest.TestCase):

    def _make_plugin(self):
        plugin = Repowise.__new__(Repowise)
        plugin.context = Context(github_token="token")
        plugin.executor = SimpleNamespace(temp_dir="/tmp/fake-venv")
        plugin._cache = {}
        return plugin

    def test_churn_heavy_detected(self):
        """
            Files with sustained, top-quartile churn (repowise's is_hotspot flag)
            count as churn-heavy; files without git history data (change_magnitude=None,
            e.g. README.md) are excluded from the ratio.
        """
        targets = {
            "src/app.py": {
                "is_hotspot": True,   # <- esto es lo que lee el código ahora
                "change_magnitude": {"lines_added_90d": 100, "lines_deleted_90d": 50},
            },
            "src/utils.py": {
                "is_hotspot": True,
                "change_magnitude": {"lines_added_90d": 30, "lines_deleted_90d": 20},
            },
            "README.md": {
                "is_hotspot": False,
                "change_magnitude": None,
            },
        }
        plugin = self._make_plugin()
        with tempfile.TemporaryDirectory() as tmp:
            fake_run = _fake_run_factory(targets)
            with patch("resqui.plugins.repowise.create_workspace") as mock_ws:
                mock_ws.return_value.__enter__ = lambda s: s
                mock_ws.return_value.__exit__ = MagicMock(return_value=False)
                mock_ws.return_value.local_path = tmp
                with patch("resqui.plugins.repowise.subprocess.run", side_effect=fake_run):
                    result = plugin.code_churn_ok("https://github.com/example/repo", "main")

        self.assertEqual(result.output, "false")  
        self.assertFalse(result.success)
        self.assertIn("2/2", result.evidence)

    def test_no_churn_heavy(self):
        """
        A file with real git history but below the hotspot floor (is_hotspot=False)
        yields a valid result.
        """
        targets = {
            "src/slow.py": {
                "is_hotspot": False,
                "change_magnitude": {"lines_added_90d": 5, "lines_deleted_90d": 2},
            },
        }
        plugin = self._make_plugin()
        with tempfile.TemporaryDirectory() as tmp:
            fake_run = _fake_run_factory(targets)
            with patch("resqui.plugins.repowise.create_workspace") as mock_ws:
                mock_ws.return_value.__enter__ = lambda s: s
                mock_ws.return_value.__exit__ = MagicMock(return_value=False)
                mock_ws.return_value.local_path = tmp
                with patch("resqui.plugins.repowise.subprocess.run", side_effect=fake_run):
                    result = plugin.code_churn_ok("https://github.com/example/repo", "main")

        self.assertEqual(result.output, "true")
        self.assertTrue(result.success)

    def test_skippable_empty_repo(self):
        """Repo without commits → handle_skip."""
        def fake_run_empty(args, **kwargs):
            if args[0] == "git" and args[1] == "clone":
                os.makedirs(args[3], exist_ok=True)
                os.makedirs(os.path.join(args[3], ".git"), exist_ok=True)
                return SimpleNamespace(stdout="", stderr="")
            if args[0] == "git" and args[1] == "rev-list":
                return SimpleNamespace(stdout="0\n", stderr="")
            return SimpleNamespace(stdout="", stderr="")

        plugin = self._make_plugin()
        with tempfile.TemporaryDirectory() as tmp:
            with patch("resqui.plugins.repowise.create_workspace") as mock_ws:
                mock_ws.return_value.__enter__ = lambda s: s
                mock_ws.return_value.__exit__ = MagicMock(return_value=False)
                mock_ws.return_value.local_path = tmp
                with patch("resqui.plugins.repowise.subprocess.run", side_effect=fake_run_empty):
                    result = plugin.code_churn_ok("https://github.com/example/repo", "main")

        self.assertEqual(result.output, "indeterminate")
        self.assertTrue(result.success)