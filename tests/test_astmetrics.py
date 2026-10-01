import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from resqui.core import Context
from resqui.plugins.astmetrics import ASTMetrics


def _fake_run_factory(average_mi_woc):
    """Builds a side_effect that simulates git clone + ast-metrics analyze."""
    def fake_run(args, **kwargs):
        cmd = args[0] if isinstance(args, list) else args
        # git clone (last argument is the destination path)
        if cmd == "git" and args[1] == "clone":
            dest = args[-1]
            os.makedirs(dest, exist_ok=True)
            return SimpleNamespace(stdout="", stderr="")
        # git checkout / any other git call
        if cmd == "git":
            return SimpleNamespace(stdout="", stderr="")
        # ast-metrics analyze: writes the report file itself, doesn't use stdout
        report_arg = next(a for a in args if a.startswith("--report-json="))
        report_path = report_arg.split("=", 1)[1]
        Path(report_path).write_text(json.dumps({
            "numberFiles": 1,
            "averageMIwoc": average_mi_woc,
        }))
        return SimpleNamespace(stdout="", stderr="")
    return fake_run


class TestASTMetricsPlugin(unittest.TestCase):

    def _make_plugin(self):
        plugin = ASTMetrics.__new__(ASTMetrics)
        plugin.context = Context(github_token="token")
        plugin.executor = SimpleNamespace(temp_dir="/tmp/fake-venv")
        plugin._cache = {}
        return plugin

    def test_maintainability_ok(self):
        """MI (without comments) at or above 65 passes."""
        plugin = self._make_plugin()
        with tempfile.TemporaryDirectory() as tmp:
            fake_run = _fake_run_factory(average_mi_woc=80)
            with patch("resqui.plugins.astmetrics.create_workspace") as mock_ws:
                mock_ws.return_value.__enter__ = lambda s: s
                mock_ws.return_value.__exit__ = MagicMock(return_value=False)
                mock_ws.return_value.local_path = tmp
                with patch("resqui.plugins.astmetrics.subprocess.run", side_effect=fake_run):
                    result = plugin.maintainability_index_ok("https://github.com/example/repo", "main")

        self.assertEqual(result.output, "true")
        self.assertTrue(result.success)

    def test_maintainability_not_ok(self):
        """MI (without comments) below 65 fails."""
        plugin = self._make_plugin()
        with tempfile.TemporaryDirectory() as tmp:
            fake_run = _fake_run_factory(average_mi_woc=50)
            with patch("resqui.plugins.astmetrics.create_workspace") as mock_ws:
                mock_ws.return_value.__enter__ = lambda s: s
                mock_ws.return_value.__exit__ = MagicMock(return_value=False)
                mock_ws.return_value.local_path = tmp
                with patch("resqui.plugins.astmetrics.subprocess.run", side_effect=fake_run):
                    result = plugin.maintainability_index_ok("https://github.com/example/repo", "main")

        self.assertEqual(result.output, "false")
        self.assertFalse(result.success)