import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "scripts" / "generate_plugins_doc.py"

spec = importlib.util.spec_from_file_location("generate_plugins_doc", SCRIPT_PATH)
generate_plugins_doc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_plugins_doc)


class TestGeneratePluginsDoc(unittest.TestCase):
    def test_plugins_doc_is_up_to_date(self):
        plugins = generate_plugins_doc._extract_plugins()
        w3id_by_abbreviation = generate_plugins_doc._fetch_w3id_by_abbreviation()
        expected = generate_plugins_doc._render_markdown(plugins, w3id_by_abbreviation)
        actual = generate_plugins_doc.OUTPUT_FILE.read_text(encoding="utf-8")
        self.assertEqual(
            actual,
            expected,
            "docs/explanation/plugins.md is stale, run "
            "`python scripts/generate_plugins_doc.py` and commit the result",
        )


if __name__ == "__main__":
    unittest.main()
