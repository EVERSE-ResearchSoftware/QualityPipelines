import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from resqui.core import CheckResult, Context, Summary


class TestCheckResult(unittest.TestCase):
    def test_defaults(self):
        r = CheckResult()
        self.assertEqual(r.process, "Undefined process")
        self.assertEqual(r.status_id, "missing")
        self.assertEqual(r.output, "missing")
        self.assertEqual(r.evidence, "missing")
        self.assertFalse(r.success)

    def test_bool_false_when_not_successful(self):
        self.assertFalse(bool(CheckResult(success=False)))

    def test_bool_true_when_successful(self):
        self.assertTrue(bool(CheckResult(success=True)))

    def test_custom_fields(self):
        r = CheckResult(
            process="my-tool",
            status_id="passing",
            output="ok",
            evidence="https://example.com",
            success=True,
        )
        self.assertEqual(r.process, "my-tool")
        self.assertEqual(r.status_id, "passing")
        self.assertTrue(r.success)


class TestContext(unittest.TestCase):
    def test_defaults_are_none(self):
        ctx = Context()
        self.assertIsNone(ctx.github_token)
        self.assertIsNone(ctx.dashverse_token)

    def test_tokens_stored(self):
        ctx = Context(github_token="gh-abc", dashverse_token="dv-xyz")
        self.assertEqual(ctx.github_token, "gh-abc")
        self.assertEqual(ctx.dashverse_token, "dv-xyz")


class TestSummary(unittest.TestCase):
    def _make_summary(self, **kwargs):
        defaults = dict(
            author="Alice",
            email="alice@example.com",
            project_name="myproject",
            repo_url="https://github.com/user/myproject",
            software_version="1.0.0",
            branch_hash_or_tag="main",
        )
        defaults.update(kwargs)
        return Summary(**defaults)

    def test_to_json_is_valid_json(self):
        s = self._make_summary()
        data = json.loads(s.to_json())
        self.assertIsInstance(data, dict)

    def test_to_json_contains_required_keys(self):
        s = self._make_summary()
        data = json.loads(s.to_json())
        self.assertEqual(data["@type"], "SoftwareQualityAssessment")
        self.assertIn("assessedSoftware", data)
        self.assertIn("checks", data)
        self.assertIn("dateCreated", data)

    def test_assessed_software_fields(self):
        s = self._make_summary(
            project_name="myproject",
            repo_url="https://github.com/user/myproject",
            software_version="2.3.0",
        )
        data = json.loads(s.to_json())
        sw = data["assessedSoftware"]
        self.assertEqual(sw["name"], "myproject")
        self.assertEqual(sw["url"], "https://github.com/user/myproject")
        self.assertEqual(sw["softwareVersion"], "2.3.0")

    def test_no_checks_by_default(self):
        s = self._make_summary()
        data = json.loads(s.to_json())
        self.assertEqual(data["checks"], [])

    def test_add_indicator_result(self):
        s = self._make_summary()
        indicator = {"@id": "https://w3id.org/everse/i/indicators/license"}
        plugin = MagicMock()
        plugin.name = "HowFairIs"
        plugin.version = "0.1.0"
        result = CheckResult(
            process="howfairis",
            status_id="passing",
            output="has license",
            evidence="LICENSE",
            success=True,
        )
        s.add_indicator_result(indicator, plugin, result)

        data = json.loads(s.to_json())
        self.assertEqual(len(data["checks"]), 1)
        check = data["checks"][0]
        self.assertEqual(check["@type"], "CheckResult")
        self.assertEqual(
            check["assessesIndicator"]["@id"],
            "https://w3id.org/everse/i/indicators/license",
        )
        self.assertEqual(check["checkingSoftware"]["name"], "HowFairIs")
        self.assertEqual(check["status"]["@id"], "passing")

    def test_write_creates_file(self):
        s = self._make_summary()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        s.write(path)
        with open(path) as f:
            data = json.load(f)
        self.assertEqual(data["@type"], "SoftwareQualityAssessment")

    def test_upload_calls_api_client(self):
        s = self._make_summary()
        with patch("resqui.core.APIClient") as MockAPIClient:
            mock_api = MagicMock()
            MockAPIClient.return_value = mock_api
            s.upload(dashverse_token="tok-123")
            MockAPIClient.assert_called_once_with("tok-123")
            mock_api.post.assert_called_once()
            payload = json.loads(mock_api.post.call_args[0][0])
            self.assertEqual(payload["@type"], "SoftwareQualityAssessment")
