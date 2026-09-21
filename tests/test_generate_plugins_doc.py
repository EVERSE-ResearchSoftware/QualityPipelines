import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "scripts" / "generate_plugins_doc.py"

spec = importlib.util.spec_from_file_location("generate_plugins_doc", SCRIPT_PATH)
generate_plugins_doc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_plugins_doc)

# Snapshot of the EVERSE vocabulary abbreviations that resolve for the
# indicators currently declared by tracked plugins, matching what
# docs/explanation/plugins.md was generated with. Kept fixed (not fetched
# live) so this test only fails on a real code/doc mismatch, not on
# unrelated upstream vocabulary changes or API outages — that live-data
# concern is covered separately by tests/test_vocabulary.py.
W3ID_BY_ABBREVIATION = {
    abbreviation: f"https://w3id.org/everse/i/indicators/{abbreviation}"
    for abbreviation in [
        "archived_in_scholarly_repository",
        "archived_in_software_heritage",
        "codemeta_completeness",
        "dependency_management",
        "descriptive_metadata",
        "has_active_communication_channels",
        "has_active_contributors",
        "has_contribution_guidelines",
        "has_no_binary_artifacts",
        "has_no_linting_issues",
        "has_published_package",
        "has_releases",
        "human_code_review_requirement",
        "listed_in_registry",
        "no_critical_vulnerability",
        "persistent_and_unique_identifier",
        "project_is_active",
        "repository_workflows",
        "requirements_specified",
        "software_has_citation",
        "software_has_documentation",
        "software_has_license",
        "software_has_tests",
        "software_is_containerized",
        "static_analysis_common_vulnerabilities",
        "support_issue_tracking",
        "uses_fuzzing",
        "uses_tool_for_warnings_and_mistakes",
        "version_control_use",
        "versioning_standards_use",
    ]
}


class TestGeneratePluginsDoc(unittest.TestCase):
    def test_plugins_doc_is_up_to_date(self):
        plugins = generate_plugins_doc._extract_plugins()
        expected = generate_plugins_doc._render_markdown(plugins, W3ID_BY_ABBREVIATION)
        actual = generate_plugins_doc.OUTPUT_FILE.read_text(encoding="utf-8")
        self.assertEqual(
            actual,
            expected,
            "docs/explanation/plugins.md is stale, run "
            "`python scripts/generate_plugins_doc.py` and commit the result",
        )


if __name__ == "__main__":
    unittest.main()
