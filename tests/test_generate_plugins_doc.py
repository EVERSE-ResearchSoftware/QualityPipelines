import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "scripts" / "generate_plugins_doc.py"

spec = importlib.util.spec_from_file_location("generate_plugins_doc", SCRIPT_PATH)
generate_plugins_doc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_plugins_doc)

# docs/explanation/plugins.md is generated (mkdocs.yml's hooks: entry calls
# generate_plugins_doc.on_pre_build before every mkdocs build/serve) and not
# committed, so there's no golden file to diff against here. These tests
# instead sanity-check the generator's own logic against the plugin sources.
W3ID_BY_ABBREVIATION = {
    "software_has_license": "https://w3id.org/everse/i/indicators/software_has_license",
    "software_has_citation": "https://w3id.org/everse/i/indicators/software_has_citation",
}


class TestGeneratePluginsDoc(unittest.TestCase):
    def test_extracts_at_least_the_always_tracked_plugins(self):
        plugins = generate_plugins_doc._extract_plugins()
        classes = {plugin["class"] for plugin in plugins}
        # Plugins that are always committed to the repo (unlike e.g. the
        # SonarQube ones, which can be local-only work in progress).
        self.assertTrue({"CFFConvert", "Gitleaks", "HowFairIs", "RSFC"} <= classes)

    def test_extracted_plugin_has_expected_shape(self):
        plugins = generate_plugins_doc._extract_plugins()
        cffconvert = next(p for p in plugins if p["class"] == "CFFConvert")
        self.assertEqual(cffconvert["indicators"], ["has_citation"])
        self.assertIn(
            "CITATION.cff", cffconvert["descriptions"]["has_citation"]
        )

    def test_render_markdown_includes_every_plugin_and_indicator(self):
        plugins = generate_plugins_doc._extract_plugins()
        markdown = generate_plugins_doc._render_markdown(plugins, W3ID_BY_ABBREVIATION)
        self.assertTrue(markdown.startswith("# Plugins & Indicators"))
        for plugin in plugins:
            self.assertIn(f"`{plugin['class']}`", markdown)
            for indicator in plugin["indicators"]:
                self.assertIn(f"`{indicator}`", markdown)

    def test_generate_writes_the_output_file(self):
        generate_plugins_doc.OUTPUT_FILE.unlink(missing_ok=True)
        generate_plugins_doc.generate()
        self.assertTrue(generate_plugins_doc.OUTPUT_FILE.exists())
        self.assertIn(
            "# Plugins & Indicators",
            generate_plugins_doc.OUTPUT_FILE.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
