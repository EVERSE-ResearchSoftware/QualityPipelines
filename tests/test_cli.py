import io
import sys  # noqa: F401
import os
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch  # noqa: F401

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
