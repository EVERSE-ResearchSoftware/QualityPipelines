import json
import subprocess
import unittest
from unittest.mock import patch

from resqui.core import Context
from resqui.plugins.openssfscorecard import OpenSSFScorecard


class TestOpenSSFScorecardToken(unittest.TestCase):
    def _plugin(self):
        plugin = OpenSSFScorecard.__new__(OpenSSFScorecard)
        plugin.context = Context(github_token="secret-token")
        plugin._cache = {}
        return plugin

    def test_token_passed_via_env_not_command_line(self):
        plugin = self._plugin()
        completed = subprocess.CompletedProcess([], 0, stdout=json.dumps({"checks": []}))

        with patch(
            "resqui.plugins.openssfscorecard.subprocess.run", return_value=completed
        ) as run:
            plugin.execute("https://github.com/example/repo", "main")

        cmd = run.call_args.args[0]
        self.assertNotIn("secret-token", " ".join(cmd))
        self.assertIn("GITHUB_TOKEN", cmd)
        self.assertEqual(run.call_args.kwargs["env"]["GITHUB_TOKEN"], "secret-token")

    def test_token_not_in_error_message(self):
        plugin = self._plugin()

        def fail(cmd, **kwargs):
            raise subprocess.CalledProcessError(1, cmd, stderr="boom")

        with patch("resqui.plugins.openssfscorecard.subprocess.run", side_effect=fail):
            with self.assertRaises(subprocess.CalledProcessError) as ctx:
                plugin.execute("https://github.com/example/repo", "main")

        self.assertNotIn("secret-token", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
