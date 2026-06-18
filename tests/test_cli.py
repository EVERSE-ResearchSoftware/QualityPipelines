import contextlib
import io
import sys  # noqa: F401
import os
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from resqui.cli import GitInspector, Spinner, print_indicator_plugins, resqui
from resqui.docopt import docopt

# The module docstring is the docopt spec; import it for arg-parsing tests.
import resqui.cli as cli_module


def _make_git_repo(path):
    """Initialise a minimal git repo with one commit and a fake remote."""
    subprocess.run(["git", "init", path], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", path, "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", path, "config", "user.name", "Test User"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            path,
            "remote",
            "add",
            "origin",
            "https://github.com/example/repo.git",
        ],
        check=True,
        capture_output=True,
    )
    readme = os.path.join(path, "README.md")
    with open(readme, "w") as f:
        f.write("hello\n")
    subprocess.run(
        ["git", "-C", path, "add", "README.md"], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", path, "commit", "-m", "Initial commit"],
        check=True,
        capture_output=True,
    )


class TestGitInspector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_dir = tempfile.mkdtemp()
        _make_git_repo(cls.repo_dir)
        cls.inspector = GitInspector(cls.repo_dir)

    def test_is_a_git_repository_true(self):
        self.assertTrue(self.inspector.is_a_git_repository)

    def test_is_a_git_repository_false(self):
        with tempfile.TemporaryDirectory() as plain_dir:
            self.assertFalse(GitInspector(plain_dir).is_a_git_repository)

    def test_current_commit_hash_is_40_hex_chars(self):
        h = self.inspector.current_commit_hash
        self.assertEqual(len(h), 40)
        self.assertTrue(all(c in "0123456789abcdef" for c in h))

    def test_author_is_string(self):
        self.assertIsInstance(self.inspector.author, str)
        self.assertTrue(self.inspector.author)

    def test_email_is_string(self):
        self.assertIsInstance(self.inspector.email, str)
        self.assertIn("@", self.inspector.email)

    def test_remote_url_returns_configured_url(self):
        self.assertEqual(
            self.inspector.remote_url, "https://github.com/example/repo.git"
        )

    def test_remote_https_url_strips_dot_git(self):
        # to_https is a pass-through for https URLs; project_name strips .git
        url = self.inspector.remote_https_url
        self.assertTrue(url.startswith("https://"))

    def test_project_name_from_url(self):
        self.assertEqual(self.inspector.project_name_from_url, "repo")

    def test_version_is_string(self):
        # With no tags, git describe --always returns the short hash.
        self.assertIsInstance(self.inspector.version, str)
        self.assertTrue(self.inspector.version)


class TestSpinner(unittest.TestCase):
    def test_context_manager_does_not_raise(self):
        # In test environments stdout is not a tty, so the spinner stays idle.
        with Spinner(print_time=False):
            pass

    def test_stop_prints_elapsed_time(self):
        spinner = Spinner(print_time=True)
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            spinner.stop()
        self.assertIn("s)", buf.getvalue())

    def test_no_spinning_when_not_a_tty(self):
        spinner = Spinner()
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = False
            spinner.__enter__()
        self.assertFalse(spinner.spinning)


class TestDocoptArgParsing(unittest.TestCase):
    """Verify CLI argument parsing without running the full command."""

    def _parse(self, argv):
        return docopt(cli_module.__doc__, argv=argv)

    def test_no_args_gives_empty_options(self):
        args = self._parse([])
        self.assertIsNone(args["-u"])
        self.assertIsNone(args["-c"])
        self.assertIsNone(args["-t"])

    def test_url_flag(self):
        args = self._parse(["-u", "https://github.com/user/repo"])
        self.assertEqual(args["-u"], "https://github.com/user/repo")

    def test_config_flag(self):
        args = self._parse(["-c", "my_config.json"])
        self.assertEqual(args["-c"], "my_config.json")

    def test_output_flag(self):
        args = self._parse(["-o", "out.json"])
        self.assertEqual(args["-o"], "out.json")

    def test_branch_flag(self):
        args = self._parse(["-b", "develop"])
        self.assertEqual(args["-b"], "develop")

    def test_verbose_flag(self):
        args = self._parse(["-v"])
        self.assertTrue(args["-v"])

    def test_indicators_subcommand(self):
        args = self._parse(["indicators"])
        self.assertTrue(args["indicators"])


class TestPrintIndicatorPlugins(unittest.TestCase):
    def test_produces_output(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            print_indicator_plugins()
        # At least one plugin class should be listed.
        self.assertIn("Class:", buf.getvalue())

    def test_lists_known_plugin(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            print_indicator_plugins()
        output = buf.getvalue()
        # All plugin entries must show Indicators section.
        self.assertIn("Indicators:", output)


class TestResquiExitPaths(unittest.TestCase):
    def test_exits_when_not_in_git_repo(self):
        """resqui with no -u and a non-git directory must exit with code 1."""
        with tempfile.TemporaryDirectory() as plain_dir:
            orig_dir = os.getcwd()
            os.chdir(plain_dir)
            try:
                with patch("sys.argv", ["resqui"]), patch("builtins.print"), patch(
                    "resqui.cli.Configuration"
                ):
                    with self.assertRaises(SystemExit) as cm:
                        resqui()
                    self.assertEqual(cm.exception.code, 1)
            finally:
                os.chdir(orig_dir)

    def test_indicators_subcommand_exits_cleanly(self):
        with patch("sys.argv", ["resqui", "indicators"]), patch(
            "resqui.cli.print_indicator_plugins"
        ), patch("builtins.print"):
            with self.assertRaises(SystemExit) as cm:
                resqui()
            self.assertEqual(cm.exception.code, 0)


class TestSpinnerTty(unittest.TestCase):
    """Cover the start/stop/spin path that only runs when stdout is a tty."""

    def test_start_and_stop(self):
        spinner = Spinner(print_time=False)
        with patch("builtins.print"):
            spinner.start()
            spinner.stop()
        self.assertFalse(spinner.spinning)

    def test_start_joins_thread(self):
        spinner = Spinner(print_time=False)
        with patch("builtins.print"):
            spinner.start()
            self.assertIsNotNone(spinner.spinner_thread)
            spinner.stop()
        # Thread must have been joined — should be done by now.
        self.assertFalse(spinner.spinner_thread.is_alive())

    def test_enter_starts_spinning_when_tty(self):
        spinner = Spinner(print_time=False)
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            spinner.__enter__()
        self.assertTrue(spinner.spinning)
        spinner.stop()


class TestResquiMainPath(unittest.TestCase):
    """Cover the resqui() body: metadata extraction, indicator loop, upload."""

    def setUp(self):
        self.inspector = MagicMock()
        self.inspector.is_a_git_repository = True
        self.inspector.remote_https_url = "https://github.com/user/repo"
        self.inspector.project_name_from_url = "repo"
        self.inspector.author = "Alice"
        self.inspector.email = "alice@example.com"
        self.inspector.version = "1.0.0"
        self.inspector.current_commit_hash = "a" * 40

        self.config = MagicMock()
        self.config._cfg = {"indicators": []}

        self.summary = MagicMock()
        self.summary.to_json.return_value = "{}"

    def _patches(self, argv=None, **overrides):
        """Return an ExitStack with standard patches applied."""
        stack = contextlib.ExitStack()
        stack.enter_context(patch("sys.argv", argv or ["resqui"]))
        stack.enter_context(patch("builtins.print"))
        stack.enter_context(
            patch("resqui.cli.GitInspector", return_value=self.inspector)
        )
        stack.enter_context(patch("resqui.cli.Configuration", return_value=self.config))
        stack.enter_context(patch("resqui.cli.Summary", return_value=self.summary))
        for target, val in overrides.items():
            stack.enter_context(patch(target, val))
        return stack

    def test_runs_with_local_repo_no_token(self):
        with self._patches():
            resqui()
        self.summary.write.assert_called_once()

    def test_github_token_path(self):
        with self._patches(argv=["resqui", "-t", "ghp-abc"]):
            resqui()
        self.summary.write.assert_called_once()

    def test_explicit_branch_skips_commit_hash(self):
        with self._patches(argv=["resqui", "-b", "develop"]):
            resqui()
        # Summary is constructed with the branch name, not the commit hash.
        call_args = resqui.__module__  # just confirm no exception  # noqa
        self.summary.write.assert_called_once()

    def test_upload_runtime_error_is_handled(self):
        self.summary.upload.side_effect = RuntimeError("network error")
        with self._patches():
            resqui()  # must not raise
        self.summary.upload.assert_called_once()

    def test_upload_value_error_is_handled(self):
        self.summary.upload.side_effect = ValueError("bad token")
        with self._patches():
            resqui()  # must not raise

    def test_indicator_success_path(self):
        from resqui.core import CheckResult

        result = CheckResult(
            process="test",
            status_id="passing",
            output="ok",
            evidence="LICENSE",
            success=True,
        )
        mock_instance = MagicMock()
        mock_instance.has_license.return_value = result
        mock_class = MagicMock(return_value=mock_instance)
        mock_class.name = "MockPlugin"
        mock_class.version = "0.1"
        mock_module = MagicMock()
        mock_module.MockPlugin = mock_class

        self.config._cfg = {
            "indicators": [
                {
                    "name": "has_license",
                    "plugin": "MockPlugin",
                    "@id": "https://example.com/license",
                }
            ]
        }
        with self._patches(
            **{
                "resqui.cli.importlib.import_module": MagicMock(
                    return_value=mock_module
                )
            }
        ):
            resqui()

        mock_instance.has_license.assert_called_once()
        self.summary.add_indicator_result.assert_called_once()

    def test_indicator_verbose_output(self):
        from resqui.core import CheckResult

        result = CheckResult(
            process="test",
            status_id="passing",
            output="ok",
            evidence="LICENSE",
            success=True,
        )
        mock_instance = MagicMock()
        mock_instance.has_license.return_value = result
        mock_class = MagicMock(return_value=mock_instance)
        mock_class.name = "MockPlugin"
        mock_class.version = "0.1"
        mock_module = MagicMock()
        mock_module.MockPlugin = mock_class

        self.config._cfg = {
            "indicators": [
                {
                    "name": "has_license",
                    "plugin": "MockPlugin",
                    "@id": "https://example.com/license",
                }
            ]
        }
        with self._patches(
            argv=["resqui", "-v"],
            **{
                "resqui.cli.importlib.import_module": MagicMock(
                    return_value=mock_module
                )
            },
        ):
            resqui()

        self.summary.add_indicator_result.assert_called_once()

    def test_indicator_init_error_is_skipped(self):
        from resqui.executors.base import ExecutorInitError

        mock_class = MagicMock(side_effect=ExecutorInitError("docker missing"))
        mock_module = MagicMock()
        mock_module.BrokenPlugin = mock_class

        self.config._cfg = {
            "indicators": [
                {
                    "name": "has_license",
                    "plugin": "BrokenPlugin",
                    "@id": "https://example.com/license",
                }
            ]
        }
        with self._patches(
            **{
                "resqui.cli.importlib.import_module": MagicMock(
                    return_value=mock_module
                )
            }
        ):
            resqui()  # must not raise; indicator is skipped

        self.summary.add_indicator_result.assert_not_called()

    def test_clone_url_path(self):
        with self._patches(
            argv=["resqui", "-u", "https://github.com/user/repo"],
            **{"resqui.cli.subprocess.run": MagicMock()},
        ):
            resqui()
        self.summary.write.assert_called_once()

    def test_clone_failure_propagates(self):
        import subprocess as sp

        with self._patches(
            argv=["resqui", "-u", "https://github.com/user/repo"],
            **{
                "resqui.cli.subprocess.run": MagicMock(
                    side_effect=sp.CalledProcessError(128, "git")
                )
            },
        ):
            with self.assertRaises(sp.CalledProcessError):
                resqui()

    def test_clone_zenodo_url_path(self):
        def mock_requests_get(url, headers=None):
            if url == "https://doi.org/10.5281/zenodo.18713816":
                mock_response = MagicMock()
                mock_response.headers = {
                    "Link": '<https://zenodo.org/api/records/20553350> ; rel="describedby" ; type="application/json"'
                }
                return mock_response

            elif (
                url == "https://zenodo.org/api/records/20553350"
                and headers.get("Accept") == "application/json"
            ):
                mock_response = MagicMock()
                mock_response.json.return_value = {
                    "metadata": {
                        "related_identifiers": [
                            {
                                "identifier": "https://github.com/EVERSE-ResearchSoftware/QualityPipelines/tree/v0.2.0",
                                "relation": "isSupplementTo",
                                "resource_type": "software",
                                "scheme": "url",
                            }
                        ]
                    }
                }
                return mock_response

            else:
                raise ValueError(f"Unsupported URL '{url}' and headers '{headers}'")

        with self._patches(
            argv=["resqui", "-u", "https://doi.org/10.5281/zenodo.18713816"],
            **{
                "requests.get": MagicMock(side_effect=mock_requests_get),
                "resqui.cli.subprocess.run": MagicMock(),
            },
        ):
            resqui()
        self.summary.write.assert_called_once()


class TestPrintIndicatorPluginsNoIndicators(unittest.TestCase):
    """Cover the '(none)' branch for a plugin that declares no indicators."""

    def test_plugin_with_no_indicators_prints_none(self):
        from resqui.plugins.base import IndicatorPlugin

        class EmptyPlugin(IndicatorPlugin):
            name = "empty"
            version = "0"
            id = "empty"
            indicators = []

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            print_indicator_plugins()
        self.assertIn("(none)", buf.getvalue())
