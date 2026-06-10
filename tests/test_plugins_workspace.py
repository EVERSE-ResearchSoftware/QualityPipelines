import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from resqui.core import Context
from resqui.plugins.gitleaks import Gitleaks
from resqui.plugins.rsfc import RSFC
from resqui.plugins.superlinter import SuperLinter


class FakeExecutor:
    def __init__(self, stdout="", stderr=""):
        self.stdout = stdout
        self.stderr = stderr
        self.calls = []

    def run(self, command, run_args=None):
        run_args = run_args or []
        self.calls.append((command, run_args))
        return SimpleNamespace(stdout=self.stdout, stderr=self.stderr)


class TestPluginSharedWorkspace(unittest.TestCase):
    def _env(self, root):
        return {
            "RESQUI_SHARED_WORKDIR": root,
            "RESQUI_DOCKER_WORK_VOLUME": "sqoo_resqui_work",
        }

    def test_gitleaks_uses_shared_workspace_volume(self):
        def fake_clone(args, **kwargs):
            os.makedirs(args[3], exist_ok=True)
            with open(os.path.join(args[3], "report.json"), "w") as f:
                json.dump([], f)

        plugin = Gitleaks.__new__(Gitleaks)
        plugin.context = Context(github_token="token")
        plugin.executor = FakeExecutor(stderr="no leaks found")

        with tempfile.TemporaryDirectory() as root:
            with patch.dict(os.environ, self._env(root), clear=True):
                with patch("resqui.plugins.gitleaks.subprocess.run", side_effect=fake_clone):
                    plugin.has_no_security_leak("https://github.com/example/repo", "main")

        command, run_args = plugin.executor.calls[0]
        self.assertEqual(run_args, ["--rm", "-v", f"sqoo_resqui_work:{root}"])
        self.assertTrue(command[1].startswith(root))
        self.assertTrue(command[3].startswith(root))

    def test_superlinter_uses_shared_workspace_volume(self):
        plugin = SuperLinter.__new__(SuperLinter)
        plugin.context = Context(github_token="token")
        plugin.executor = FakeExecutor(stdout="")

        with tempfile.TemporaryDirectory() as root:
            with patch.dict(os.environ, self._env(root), clear=True):
                with patch("resqui.plugins.superlinter.subprocess.run"):
                    plugin.has_no_linting_issues("https://github.com/example/repo", "main")

        _, run_args = plugin.executor.calls[0]
        self.assertIn("--rm", run_args)
        self.assertIn("-v", run_args)
        self.assertIn(f"sqoo_resqui_work:{root}", run_args)
        self.assertIn("-e", run_args)
        workspace_index = run_args.index("-e", run_args.index("DEFAULT_BRANCH=main") + 1)
        self.assertTrue(run_args[workspace_index + 1].startswith("DEFAULT_WORKSPACE=" + root))

    def test_rsfc_uses_shared_workspace_volume(self):
        def fake_rsfc_run(command, run_args=None):
            run_args = run_args or []
            workdir = run_args[run_args.index("-w") + 1]
            output_dir = os.path.join(workdir, "rsfc_output")
            os.makedirs(output_dir, exist_ok=True)
            assessment_path = os.path.join(output_dir, "rsfc_assessment.json")
            with open(assessment_path, "w") as f:
                json.dump({"checks": []}, f)
            fake_executor.calls.append((command, run_args))
            return SimpleNamespace(stdout="", stderr="")

        fake_executor = FakeExecutor()
        fake_executor.run = fake_rsfc_run

        plugin = RSFC.__new__(RSFC)
        plugin.context = Context(github_token="token")
        plugin.executor = fake_executor
        plugin._cache = {}

        with tempfile.TemporaryDirectory() as root:
            with patch.dict(os.environ, self._env(root), clear=True):
                plugin.execute("https://github.com/example/repo", "main")

        _, run_args = fake_executor.calls[0]
        self.assertIn("-v", run_args)
        self.assertIn(f"sqoo_resqui_work:{root}", run_args)
        self.assertIn("-w", run_args)
        self.assertTrue(run_args[run_args.index("-w") + 1].startswith(root))
