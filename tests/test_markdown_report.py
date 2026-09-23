import json
import tempfile
import unittest
from pathlib import Path

from resqui.markdown_report import render, convert


SAMPLE = {
    "dateCreated": "2026-01-01 00:00:00",
    "assessedSoftware": {
        "name": "myproject",
        "url": "https://github.com/user/myproject",
        "softwareVersion": "1.0.0",
    },
    "checks": [
        {
            "assessesIndicator": {"@id": "https://w3id.org/everse/i/indicators/license"},
            "checkingSoftware": {"name": "HowFairIs", "version": "0.14.2"},
            "status": {"@id": "schema:CompletedActionStatus"},
            "output": "valid",
            "evidence": "Found license file: 'LICENSE'.",
        },
        {
            "assessesIndicator": {"@id": "https://w3id.org/everse/i/indicators/citation"},
            "checkingSoftware": {"name": "CFFConvert", "version": "2.0.0"},
            "status": {"@id": "schema:FailedActionStatus"},
            "output": "invalid",
            "evidence": "No valid CITATION.cff | file found.",
        },
    ],
}


class TestRender(unittest.TestCase):
    def test_contains_title_and_run_information(self):
        markdown = render(SAMPLE)
        self.assertIn("# Software Quality Assessment", markdown)
        self.assertIn("- Project: myproject", markdown)
        self.assertIn("- Repository: https://github.com/user/myproject", markdown)

    def test_pass_fail_counts(self):
        markdown = render(SAMPLE)
        self.assertIn("- Checks: 1/2 successful (1 failed)", markdown)

    def test_status_column(self):
        markdown = render(SAMPLE)
        self.assertIn("| PASS |", markdown)
        self.assertIn("| FAIL |", markdown)

    def test_completed_check_with_false_output_fails(self):
        data = {
            "checks": [
                {
                    "status": {"@id": "schema:CompletedActionStatus"},
                    "output": output,
                }
                for output in ["true", "false", "secure", "insecure"]
            ]
        }
        markdown = render(data)
        self.assertIn("- Checks: 2/4 successful (2 failed)", markdown)

    def test_escapes_pipe_characters_in_evidence(self):
        markdown = render(SAMPLE)
        self.assertIn("No valid CITATION.cff \\| file found.", markdown)

    def test_escapes_backslash_before_pipe(self):
        from resqui.markdown_report import _escape

        self.assertEqual(_escape("a\\|b"), "a\\\\\\|b")

    def test_empty_checks(self):
        markdown = render({"assessedSoftware": {}, "checks": []})
        self.assertIn("- Checks: 0/0 successful (0 failed)", markdown)


class TestConvert(unittest.TestCase):
    def test_reads_json_and_writes_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "summary.json"
            output_path = Path(tmp) / "summary.md"
            input_path.write_text(json.dumps(SAMPLE))

            convert(input_path, output_path)

            content = output_path.read_text()
            self.assertIn("# Software Quality Assessment", content)
            self.assertIn("myproject", content)

    def test_rejects_identical_input_and_output_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(SAMPLE))

            with self.assertRaises(ValueError):
                convert(path, path)
