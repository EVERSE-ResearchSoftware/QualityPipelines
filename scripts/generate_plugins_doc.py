#!/usr/bin/env python3
"""Generate the Plugins & Indicators reference doc from plugin source files."""

from __future__ import annotations

import ast
from pathlib import Path

import requests

from resqui.vocabulary import fetch_indicator_id_by_abbreviation

ROOT = Path(__file__).resolve().parent.parent
PLUGINS_DIR = ROOT / "src" / "resqui" / "plugins"
OUTPUT_FILE = ROOT / "docs" / "explanation" / "plugins.md"

INTRO = """\
An **indicator** is a measurable property of a software repository. resqui maps
each indicator to a plugin method that performs the check automatically.\
"""

INTERPRETING_RESULTS = """\
## Interpreting results

Each indicator produces a `CheckResult` with:

| Field | Meaning |
|---|---|
| `output` | The [EVERSE assessment schema](https://github.com/EVERSE-ResearchSoftware/schemas/blob/main/assessment/dev/README.md) defines this as `true` / `false` / `indeterminate`. Most plugins (OpenSSFScorecard, SuperLinter, RSFC, OEBFAIR) follow that; a few don't yet and emit their own strings instead — `valid`/`invalid` (CFFConvert, HowFairIs, SonarQube), `secure`/`insecure` (Gitleaks). Treat those as known drift from the schema, not an intentional per-plugin vocabulary. `missing` is the `CheckResult` default before a plugin sets it, not a value plugins return on purpose. |
| `status` | A Schema.org action status IRI. `schema:CompletedActionStatus` means the check ran to completion — **not** that it passed; the schema's own example uses it for both a passing and a failing check. Check `output`/`success`, not `status`, to know whether an indicator passed. |
| `evidence` | Human-readable finding from the underlying tool |

A failing indicator does **not** abort the run — all configured indicators
are always attempted.\
"""

STATUS_IDS = """\
## Status IDs

| Status IRI | Meaning |
|---|---|
| `schema:CompletedActionStatus` | The check ran to completion — used for both pass and fail outcomes |
| `schema:FailedActionStatus` | The check itself failed to run or complete (e.g. an exception during the check), not a normal "indicator not satisfied" result |
| `missing` | `CheckResult` default before a field is set; not typically emitted by plugins |\
"""

W3ID_NOTE = """\
Indicators are matched to the [EVERSE indicator vocabulary](https://everse.software/indicators/api/indicators.json)
by exact name. Some plugins use internal aliases or plugin-specific
extensions that don't match a vocabulary abbreviation exactly (for example
`has_license` vs. the vocabulary's `software_has_license`, or SonarQube's
`code_quality_grade`, which has no vocabulary equivalent) — these show `-` in
the W3ID column rather than a guessed link.\
"""

# Page-only tweaks to the readthedocs theme: use the full window width and let
# table cells wrap, so the long indicator lists fit without scrolling.
PAGE_STYLE = """\
<style>
.wy-nav-content { max-width: none; }
.wy-table-responsive table td, .wy-table-responsive table th { white-space: normal; }
details[id^="plugin-"]:last-of-type { margin-bottom: 2em; }
</style>\
"""

# Opens the collapsed plugin section a summary-table link points to. The click
# handler covers the theme swallowing the hashchange; the hash check covers
# direct links to the page.
OPEN_DETAILS_SCRIPT = """\
<script>
function openPlugin(id) {
  const target = document.getElementById(id);
  if (target && target.tagName === "DETAILS") {
    target.open = true;
    target.scrollIntoView();
  }
}
document.querySelectorAll('a[href^="#plugin-"]').forEach((link) => {
  link.addEventListener("click", () => openPlugin(link.getAttribute("href").slice(1)));
});
if (location.hash) openPlugin(location.hash.slice(1));
window.addEventListener("hashchange", () => openPlugin(location.hash.slice(1)));
</script>\
"""


def _literal_value(node: ast.AST):
    """Return Python value for simple literals, otherwise None."""
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return None


def _inherits_indicator_plugin(node: ast.ClassDef) -> bool:
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "IndicatorPlugin":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "IndicatorPlugin":
            return True
    return False


def _is_check_result_call(call: ast.Call) -> bool:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id == "CheckResult"
    if isinstance(func, ast.Attribute):
        return func.attr == "CheckResult"
    return False


def _describe_indicator(method: ast.FunctionDef) -> str | None:
    """Pull the CheckResult(process=...) description out of an indicator method.

    Handles both a literal passed straight to CheckResult and one first
    assigned to a local `process` variable (as sonarqube.py does).
    """
    process_var: str | None = None
    for node in ast.walk(method):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "process"
        ):
            value = _literal_value(node.value)
            if isinstance(value, str):
                process_var = value

    for node in ast.walk(method):
        if not isinstance(node, ast.Call) or not _is_check_result_call(node):
            continue
        for kw in node.keywords:
            if kw.arg != "process":
                continue
            value = _literal_value(kw.value)
            if isinstance(value, str):
                return value
            if isinstance(kw.value, ast.Name) and kw.value.id == "process" and process_var:
                return process_var
    return None


def _extract_plugins() -> list[dict[str, object]]:
    plugins: list[dict[str, object]] = []
    for path in sorted(PLUGINS_DIR.glob("*.py")):
        if path.name in {"__init__.py", "base.py"}:
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if not _inherits_indicator_plugin(node):
                continue

            indicators: list[str] = []
            requires: list[str] = []
            plugin_id = None
            version = None

            for stmt in node.body:
                if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                    continue
                target = stmt.targets[0]
                if not isinstance(target, ast.Name):
                    continue

                value = _literal_value(stmt.value)
                if target.id == "indicators" and isinstance(value, (list, tuple)):
                    indicators = [str(item) for item in value]
                elif target.id == "requires" and isinstance(value, (list, tuple)):
                    requires = [str(item) for item in value]
                elif target.id == "id" and isinstance(value, str):
                    plugin_id = value
                elif target.id == "version" and isinstance(value, str):
                    version = value

            methods_by_name = {
                stmt.name: stmt
                for stmt in node.body
                if isinstance(stmt, ast.FunctionDef)
            }
            descriptions = {
                indicator: _describe_indicator(methods_by_name[indicator])
                for indicator in indicators
                if indicator in methods_by_name
            }

            plugins.append(
                {
                    "class": node.name,
                    "file": path.name,
                    "description": ast.get_docstring(node),
                    "version": version,
                    "id": plugin_id,
                    "indicators": indicators,
                    "descriptions": descriptions,
                    "requires": requires,
                }
            )

    return plugins




def _anchor(plugin: dict[str, object]) -> str:
    return f"plugin-{str(plugin['class']).lower()}"


def _render_markdown(plugins: list[dict[str, object]], w3id_by_abbreviation: dict[str, str]) -> str:
    lines = [
        "# Plugins & Indicators",
        "",
        PAGE_STYLE,
        "",
        "This page is auto-generated from `src/resqui/plugins/` during docs build.",
        "",
        INTRO,
        "",
        "## Plugins",
        "",
        "Click a plugin name to see its description and the checks behind each indicator.",
        "",
        "| Plugin | Version | ID | Requires | Indicators |",
        "|---|---|---|---|---|",
    ]

    for plugin in plugins:
        version = f"`{plugin['version']}`" if plugin["version"] else "-"
        plugin_id = f"[{plugin['id']}]({plugin['id']})" if plugin["id"] else "-"
        requires = plugin["requires"]
        requires_text = ", ".join(f"`{item}`" for item in requires) if requires else "-"
        indicators = plugin["indicators"]
        indicator_text = ", ".join(f"`{item}`" for item in indicators) if indicators else "-"
        lines.append(
            f"| [`{plugin['class']}`](#{_anchor(plugin)}) | {version} | {plugin_id} "
            f"| {requires_text} | {indicator_text} |"
        )

    lines.extend(["", "## Plugin details", "", W3ID_NOTE, ""])

    for plugin in plugins:
        descriptions = plugin["descriptions"]
        lines.extend(
            [
                f'<details id="{_anchor(plugin)}" markdown="1">',
                f"<summary><strong>{plugin['class']}</strong></summary>",
                "",
            ]
        )
        if plugin["description"]:
            lines.extend([plugin["description"], ""])
        lines.extend([f"Source file: `{plugin['file']}`", ""])
        if plugin["indicators"]:
            lines.extend(
                [
                    "| Indicator | What it checks | W3ID |",
                    "|---|---|---|",
                ]
            )
            for indicator in plugin["indicators"]:
                description = descriptions.get(indicator)
                text = description.replace("|", "\\|") if description else "-"
                w3id = w3id_by_abbreviation.get(indicator)
                w3id_text = f"[`{indicator}`]({w3id})" if w3id else "-"
                lines.append(f"| `{indicator}` | {text} | {w3id_text} |")
            lines.append("")
        lines.extend(["</details>", ""])

    lines.append(OPEN_DETAILS_SCRIPT)
    lines.append("")
    lines.append(INTERPRETING_RESULTS)
    lines.append("")
    lines.append(STATUS_IDS)

    return "\n".join(lines).rstrip() + "\n"


def generate() -> None:
    """Regenerate docs/explanation/plugins.md from the plugin sources."""
    plugins = _extract_plugins()
    try:
        w3id_by_abbreviation = fetch_indicator_id_by_abbreviation()
    except requests.RequestException as error:
        raise RuntimeError(
            f"Could not fetch the EVERSE indicator vocabulary: {error}\n"
            "Refusing to generate docs/explanation/plugins.md with missing "
            "W3ID links — retry once the vocabulary API is reachable."
        ) from error
    markdown = _render_markdown(plugins, w3id_by_abbreviation)
    # Rewriting an unchanged file would make `mkdocs serve` rebuild forever.
    if OUTPUT_FILE.exists() and OUTPUT_FILE.read_text(encoding="utf-8") == markdown:
        return
    OUTPUT_FILE.write_text(markdown, encoding="utf-8")
    print(f"Generated {OUTPUT_FILE.relative_to(ROOT)} ({len(plugins)} plugins)")


def on_pre_build(config, **kwargs) -> None:
    """mkdocs hook (see the `hooks:` entry in mkdocs.yml): regenerate the
    plugins reference before every `mkdocs build`/`mkdocs serve`, so it can
    never go stale relative to what actually gets deployed."""
    generate()


def main() -> None:
    generate()


if __name__ == "__main__":
    main()
