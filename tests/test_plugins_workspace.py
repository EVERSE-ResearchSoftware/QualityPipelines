import json
import os
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from resqui.core import Context
from resqui.plugins.gitleaks import Gitleaks
from resqui.plugins.howfairis import HowFairIs
from resqui.plugins.rsfc import RSFC
from resqui.plugins.rsmetacheck import Rsmetacheck
from resqui.plugins.scancodetoolkit import ScanCodeToolkit
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


class FakePythonExecutor:
    def __init__(self, stdout="", stderr=""):
        self.stdout = stdout
        self.stderr = stderr
        self.scripts = []

    def execute(self, script):
        self.scripts.append(script)
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

        command, run_args = fake_executor.calls[0]
        self.assertIn("-v", run_args)
        self.assertIn(f"sqoo_resqui_work:{root}", run_args)
        self.assertIn("-w", run_args)
        self.assertTrue(run_args[run_args.index("-w") + 1].startswith(root))
        self.assertIn("-t", command)
        self.assertEqual(command[command.index("-t") + 1], "token")

    def test_rsfc_runs_without_token(self):
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
        plugin.context = Context(github_token=None)
        plugin.executor = fake_executor
        plugin._cache = {}

        with tempfile.TemporaryDirectory() as root:
            with patch.dict(os.environ, self._env(root), clear=True):
                plugin.execute("https://github.com/example/repo", "main")

        command, _ = fake_executor.calls[0]
        self.assertNotIn("-t", command)


    def test_rsmetacheck_passes_commit_hash(self):
        commit_hash = "a" * 40
        commands = []

        def fake_run(command, run_args=None):
            commands.append(command)

            workdir = run_args[run_args.index("-w") + 1]

            with open(
                os.path.join(workdir, "analysis_results.json"), "w"
            ) as f:
                json.dump({"pitfalls & warnings": []}, f)

            return SimpleNamespace(returncode=0, stdout="", stderr="")

        plugin = Rsmetacheck.__new__(Rsmetacheck)
        plugin.context = Context()
        plugin.executor = SimpleNamespace(run=fake_run)
        plugin._cache = {}

        with tempfile.TemporaryDirectory() as root:
            object.__setattr__(plugin.context, "somef_cache_dir", root)

            with patch.dict(os.environ, self._env(root), clear=True):
                plugin.execute(
                    "https://github.com/example/repo",
                    commit_hash,
                )

        command = commands[0]

        self.assertIn("--branch", command)
        self.assertEqual(
            command[command.index("--branch") + 1],
            commit_hash,
        )
    def test_rsfc_passes_commit_hash(self):
        commit_hash = "a" * 40
        commands = []

        def fake_run(command, run_args=None):
            commands.append(command)

            workdir = run_args[run_args.index("-w") + 1]
            output_dir = os.path.join(workdir, "rsfc_output")
            os.makedirs(output_dir, exist_ok=True)

            with open(
                os.path.join(output_dir, "rsfc_assessment.json"), "w"
            ) as f:
                json.dump({"checks": []}, f)

            return SimpleNamespace(returncode=0, stdout="", stderr="")

        plugin = RSFC.__new__(RSFC)
        plugin.context = Context()
        plugin.executor = SimpleNamespace(run=fake_run)
        plugin._cache = {}

        with tempfile.TemporaryDirectory() as root:
            object.__setattr__(plugin.context, "somef_cache_dir", root)

            with patch.dict(os.environ, self._env(root), clear=True):
                plugin.execute(
                    "https://github.com/example/repo",
                    commit_hash,
                )

        command = commands[0]

        self.assertIn("-b", command)
        self.assertEqual(
            command[command.index("-b") + 1],
            commit_hash,
        )

class TestHowFairIsIndicatorMappings(unittest.TestCase):
    def test_installs_howfairis_from_git_repository(self):
        with patch("resqui.plugins.howfairis.PythonExecutor") as mock_executor_class:
            mock_executor = MagicMock()
            mock_executor_class.return_value = mock_executor

            HowFairIs(Context(github_token="token"))

        mock_executor.install.assert_called_once_with(
            "git+https://github.com/fair-software/howfairis.git@0.15.0"
        )

    def test_license_for_file_types_uses_reuse_checker(self):
        plugin = HowFairIs.__new__(HowFairIs)
        plugin.executor = FakePythonExecutor(stdout="True\n")

        result = plugin.software_has_license_for_file_types(
            "https://github.com/example/repo",
            "main",
        )

        script = plugin.executor.scripts[0]
        self.assertIn("from howfairis import Repo, Checker", script)
        self.assertIn("checker.is_reuse_compliant()", script)
        self.assertTrue(result)
        self.assertEqual(result.output, "true")
        self.assertEqual(result.status_id, "schema:CompletedActionStatus")


class TestRSFCIndicatorMappings(unittest.TestCase):
    def _plugin_with_report(self, report):
        plugin = RSFC.__new__(RSFC)
        plugin.execute = lambda _url, _branch: report
        return plugin

    def _check(self, output, evidence):
        return {
            "process": f"process for {evidence}",
            "status": {"@id": "schema:CompletedActionStatus"},
            "output": output,
            "evidence": evidence,
        }

    def test_new_rsfc_indicators_map_true_outputs(self):
        report = {
            "RSFC-08-2": self._check("true", "zenodo evidence"),
            "RSFC-05-4": self._check("true", "support channel evidence"),
        }
        plugin = self._plugin_with_report(report)

        cases = [
            ("archived_in_scholarly_repository", "RSFC-08-2"),
            ("has_active_communication_channels", "RSFC-05-4"),
        ]
        for indicator, check_id in cases:
            self.assertIn(indicator, RSFC.indicators)
            result = getattr(plugin, indicator)("https://github.com/example/repo", "main")
            expected = report[check_id]

            self.assertTrue(result)
            self.assertEqual(result.process, expected["process"])
            self.assertEqual(result.status_id, expected["status"]["@id"])
            self.assertEqual(result.output, expected["output"])
            self.assertEqual(result.evidence, expected["evidence"])

    def test_new_rsfc_indicators_map_non_true_outputs(self):
        report = {
            "RSFC-08-2": self._check("false", "no zenodo evidence"),
            "RSFC-05-4": self._check("error", "no support channel evidence"),
        }
        plugin = self._plugin_with_report(report)

        cases = [
            ("archived_in_scholarly_repository", "RSFC-08-2"),
            ("has_active_communication_channels", "RSFC-05-4"),
        ]
        for indicator, check_id in cases:
            self.assertIn(indicator, RSFC.indicators)
            result = getattr(plugin, indicator)("https://github.com/example/repo", "main")
            expected = report[check_id]

            self.assertFalse(result)
            self.assertEqual(result.process, expected["process"])
            self.assertEqual(result.status_id, expected["status"]["@id"])
            self.assertEqual(result.output, expected["output"])
            self.assertEqual(result.evidence, expected["evidence"])


class TestRsmetacheckIndicatorMappings(unittest.TestCase):
    def _plugin_with_report(self, report):
        plugin = Rsmetacheck.__new__(Rsmetacheck)
        plugin.execute = lambda _url, _branch: report
        return plugin

    def _pitfall(self, code, count):
        return {
            "pitfall_code": code,
            "pitfall_desc": f"description for {code}",
            "count": count,
        }

    def _warning(self, code, count):
        return {
            "warning_code": code,
            "warning_desc": f"description for {code}",
            "count": count,
        }

    def test_metadata_is_up_to_date_passes_when_useful_findings_are_absent(self):
        report = {
            "pitfalls & warnings": [
                self._pitfall("P001", 0),
                self._pitfall("P012", 0),
                self._pitfall("P016", 0),
                self._pitfall("P017", 0),
                self._warning("W002", 0),
                self._pitfall("P999", 3),
            ]
        }
        plugin = self._plugin_with_report(report)

        result = plugin.metadata_is_up_to_date(
            "https://github.com/example/repo",
            "main",
        )

        self.assertTrue(result)
        self.assertEqual(result.status_id, "schema:CompletedActionStatus")
        self.assertEqual(result.output, "true")
        self.assertIn("P001: description for P001 (count: 0)", result.evidence)
        self.assertIn("W002: description for W002 (count: 0)", result.evidence)
        self.assertNotIn("P999", result.evidence)

    def test_metadata_is_up_to_date_fails_when_useful_findings_are_detected(self):
        report = {
            "pitfalls & warnings": [
                self._pitfall("P001", 0),
                self._pitfall("P012", 2),
                self._pitfall("P016", 0),
                self._pitfall("P017", 0),
                self._warning("W002", 1),
            ]
        }
        plugin = self._plugin_with_report(report)

        result = plugin.metadata_is_up_to_date(
            "https://github.com/example/repo",
            "main",
        )

        self.assertFalse(result)
        self.assertEqual(result.status_id, "schema:CompletedActionStatus")
        self.assertEqual(result.output, "false")
        self.assertIn("P012: description for P012 (count: 2)", result.evidence)
        self.assertIn("W002: description for W002 (count: 1)", result.evidence)
        self.assertNotIn("P001: description for P001", result.evidence)

    def test_metadata_is_up_to_date_fails_when_checks_are_missing(self):
        report = {
            "pitfalls & warnings": [
                self._pitfall("P001", 0),
                self._pitfall("P012", 0),
                self._pitfall("P016", 0),
            ]
        }

        plugin = self._plugin_with_report(report)

        result = plugin.metadata_is_up_to_date(
            "https://github.com/example/repo",
            "main",
        )

        self.assertFalse(result)
        self.assertEqual(result.status_id, "schema:FailedActionStatus")
        self.assertEqual(result.output, "error")
        self.assertIn("P017", result.evidence)
        self.assertIn("W002", result.evidence)


class TestScanCodeToolkitIndicatorMappings(unittest.TestCase):
    URL = "https://github.com/example/repo"

    def _plugin_with_report(self, report):
        plugin = ScanCodeToolkit.__new__(ScanCodeToolkit)
        plugin.execute = lambda _url, _branch: report
        return plugin

    # Returned by any execution of scancodetoolkit, per file information
    def _file(self, path, spdx=None, size=10, **flags):
        """A ScanCode file entry; `spdx` is the detected license, if any."""
        return {
            "path": path,
            "type": "file",
            "size": size,
            "extension": os.path.splitext(path)[1],
            "detected_license_expression": spdx.lower() if spdx else None,
            "detected_license_expression_spdx": spdx,
            **flags,
        }
    
    # Returned when scancodetoolkit is run with "--summary" option (used by "has_license")
    def _summary(self, declared, expression=None, score=0):
        return {
            "declared_license_expression": expression,
            "license_clarity_score": {"score": score, "declared_license": declared},
        }

    # "has_license" indicators tests
    def test_has_license_passes_when_a_declared_license_is_found(self):
        report = {
            "summary": self._summary(True, "apache-2.0", 90),
            "files": [
                self._file("LICENSE", "Apache-2.0", is_key_file=True, is_legal=True),
                self._file("setup.py", "Apache-2.0", is_key_file=True, is_source=True),
                self._file("src/main.py", is_source=True),
            ],
        }
        result = self._plugin_with_report(report).has_license(self.URL, "main")

        self.assertTrue(result)
        self.assertEqual(result.status_id, "schema:CompletedActionStatus")
        self.assertEqual(result.output, "true")
        self.assertEqual(result.raw_value, "90")
        self.assertIn("Declared license: apache-2.0", result.evidence)
        self.assertIn("LICENSE (Apache-2.0), setup.py (Apache-2.0)", result.evidence)
        self.assertNotIn("src/main.py", result.evidence)

    def test_has_license_fails_when_no_declared_license_is_found(self):
        report = {
            "summary": self._summary(False),
            "files": [self._file("main.py", is_source=True)],
        }
        result = self._plugin_with_report(report).has_license(self.URL, "main")

        self.assertFalse(result)
        self.assertEqual(result.status_id, "schema:CompletedActionStatus")
        self.assertEqual(result.output, "false")
        self.assertEqual(result.raw_value, "0")

    def test_has_license_errors_without_a_summary(self):
        report = {"files": [self._file("main.py", is_source=True)]}
        result = self._plugin_with_report(report).has_license(self.URL, "main")

        self.assertFalse(result)
        self.assertEqual(result.status_id, "schema:FailedActionStatus")
        self.assertEqual(result.output, "error")

    # "software_has_license_for_file_types" indicators tests
    def test_file_types_passes_when_every_file_is_licensed(self):
        report = {
            "files": [
                self._file("LICENSE", "MIT", is_legal=True),
                self._file("main.py", "MIT", is_source=True),
                self._file("README.md", "CC-BY-4.0", is_readme=True),
                # licensed through its REUSE companion file
                self._file("logo.png", is_media=True),
                self._file("logo.png.license", "CC0-1.0"),
                # not counted: empty file and REUSE metadata
                self._file("pkg/__init__.py", size=0, is_source=True),
                self._file("REUSE.toml"),
            ],
        }
        result = self._plugin_with_report(report).software_has_license_for_file_types(
            self.URL, "main"
        )

        self.assertTrue(result)
        self.assertEqual(result.output, "true")
        self.assertEqual(result.raw_value, "100.0")
        self.assertIn("3/3 files", result.evidence)
        self.assertIn("code: 1/1, documentation: 1/1, media: 1/1", result.evidence)
        self.assertIn("Licenses found: CC-BY-4.0, CC0-1.0, MIT", result.evidence)

    def test_file_types_fails_with_partial_coverage(self):
        report = {
            "files": [
                self._file("main.py", "MIT", is_source=True),
                self._file("utils.py", is_source=True),
                self._file("docs/guide.md"),
                self._file("data.csv"),
            ],
        }
        result = self._plugin_with_report(report).software_has_license_for_file_types(
            self.URL, "main"
        )

        self.assertFalse(result)
        self.assertEqual(result.status_id, "schema:CompletedActionStatus")
        self.assertEqual(result.output, "false")
        self.assertEqual(result.raw_value, "25.0")
        self.assertIn("code: 1/2, documentation: 0/1, other: 0/1", result.evidence)

    def test_file_types_is_indeterminate_without_files_to_check(self):
        report = {
            "files": [
                self._file("LICENSE", "MIT", is_legal=True),
                self._file("empty.py", size=0, is_source=True),
                {"path": "src", "type": "directory"},
            ],
        }
        result = self._plugin_with_report(report).software_has_license_for_file_types(
            self.URL, "main"
        )

        self.assertTrue(result)
        self.assertEqual(result.output, "indeterminate")

    def test_indicators_report_execute_errors(self):
        plugin = self._plugin_with_report({"error": "Could not clone the repository."})

        for indicator in ScanCodeToolkit.indicators:
            result = getattr(plugin, indicator)(self.URL, "main")

            self.assertFalse(result)
            self.assertEqual(result.status_id, "schema:FailedActionStatus")
            self.assertEqual(result.output, "error")
            self.assertEqual(result.evidence, "Could not clone the repository.")


class TestScanCodeToolkitExecute(unittest.TestCase):
    """Tests execute() with git and ScanCode replaced by fakes."""

    URL = "https://github.com/example/repo"

    def _plugin(self):
        plugin = ScanCodeToolkit.__new__(ScanCodeToolkit)
        plugin.context = Context(github_token=None)
        plugin.executor = SimpleNamespace(temp_dir="/tmp/fake-venv")
        plugin._cache = {}
        return plugin

    def _run(self, plugin, fake_run, indicators):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = os.path.join(tmp, "repo")
            with patch("resqui.plugins.scancodetoolkit.create_workspace") as mock_ws:
                mock_ws.return_value.__enter__ = lambda s: s
                mock_ws.return_value.__exit__ = MagicMock(return_value=False)
                mock_ws.return_value.local_path = workspace
                with patch(
                    "resqui.plugins.scancodetoolkit.subprocess.run", side_effect=fake_run
                ):
                    return [
                        getattr(plugin, indicator)(self.URL, "main")
                        for indicator in indicators
                    ]

    def test_both_indicators_share_a_single_scan(self):
        scancode_calls = []

        def fake_run(args, **kwargs):
            if args[0] == "git":
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            scancode_calls.append(args)
            report_path = args[args.index("--json") + 1]
            with open(report_path, "w") as f:
                json.dump(
                    {
                        "summary": {
                            "declared_license_expression": "mit",
                            "license_clarity_score": {"score": 100, "declared_license": True},
                        },
                        "files": [
                            {
                                "path": "main.py",
                                "type": "file",
                                "size": 10,
                                "is_source": True,
                                "is_key_file": True,
                                "detected_license_expression": "mit",
                                "detected_license_expression_spdx": "MIT",
                            }
                        ],
                    },
                    f,
                )
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        results = self._run(self._plugin(), fake_run, ScanCodeToolkit.indicators)

        self.assertEqual(len(scancode_calls), 1)
        self.assertIn("--summary", scancode_calls[0])
        self.assertTrue(all(results))

    def test_clone_failure_is_reported_as_error(self):
        def fake_run(args, **kwargs):
            raise subprocess.CalledProcessError(128, args)

        [result] = self._run(self._plugin(), fake_run, ["has_license"])

        self.assertEqual(result.output, "error")
        self.assertIn("Could not clone", result.evidence)

    def test_missing_report_is_reported_as_error(self):
        def fake_run(args, **kwargs):
            if args[0] == "git":
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="scancode crashed")

        [result] = self._run(self._plugin(), fake_run, ["has_license"])

        self.assertEqual(result.output, "error")
        self.assertIn("did not produce a report", result.evidence)
        self.assertIn("scancode crashed", result.evidence)


class TestSomefCacheIdentifiers(unittest.TestCase):

    def setUp(self):
        self.rsfc = RSFC.__new__(RSFC)
        self.rsmetacheck = Rsmetacheck.__new__(Rsmetacheck)

    def test_different_branches_have_different_ids(self):
        refs = ["feature/develop", "feature_develop"]

        for plugin in (self.rsfc, self.rsmetacheck):
            self.assertNotEqual(
                plugin.ref_id(refs[0]),
                plugin.ref_id(refs[1]),
            )

    def test_different_repositories_have_different_ids(self):
        urls = [
            "https://github.com/a_b/c",
            "https://github.com/a/b_c",
        ]

        for plugin in (self.rsfc, self.rsmetacheck):
            self.assertNotEqual(
                plugin.software_id(urls[0]),
                plugin.software_id(urls[1]),
            )

    def test_plugins_generate_same_cache_ids(self):
        url = "https://github.com/example/repo"
        ref = "feature/develop"

        self.assertEqual(
            self.rsfc.software_id(url),
            self.rsmetacheck.software_id(url),
        )

        self.assertEqual(
            self.rsfc.ref_id(ref),
            self.rsmetacheck.ref_id(ref),
        )
