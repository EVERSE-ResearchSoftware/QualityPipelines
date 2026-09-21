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

| Field | Values |
|---|---|
| `output` | `valid` — indicator satisfied; `missing` — not found; `failed` — check error |
| `status` | Schema.org action status IRI |
| `evidence` | Human-readable finding from the underlying tool |

An indicator returning `missing` or `failed` does **not** abort the run — all
configured indicators are always attempted.\
"""

STATUS_IDS = """\
## Status IDs

| Status IRI | Meaning |
|---|---|
| `schema:CompletedActionStatus` | Check passed |
| `schema:FailedActionStatus` | Check ran but found a problem |
| `missing` | Check could not be completed (plugin skipped) |\
"""

W3ID_NOTE = """\
Indicators are matched to the [EVERSE indicator vocabulary](https://everse.software/indicators/api/indicators.json)
by exact name. Some plugins use internal aliases or plugin-specific
extensions that don't match a vocabulary abbreviation exactly (for example
`has_license` vs. the vocabulary's `software_has_license`, or SonarQube's
`code_quality_grade`, which has no vocabulary equivalent) — these show `-` in
the W3ID column rather than a guessed link.\
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
                    "version": version,
                    "id": plugin_id,
                    "indicators": indicators,
                    "descriptions": descriptions,
                    "requires": requires,
                }
            )

    return plugins


def _fetch_w3id_by_abbreviation() -> dict[str, str]:
    try:
        return fetch_indicator_id_by_abbreviation()
    except requests.RequestException:
        return {}


def _render_markdown(plugins: list[dict[str, object]], w3id_by_abbreviation: dict[str, str]) -> str:
    lines = [
        "# Plugins & Indicators",
        "",
        "This page is auto-generated from `src/resqui/plugins/` during docs build.",
        "",
        INTRO,
        "",
        "## Plugin to indicator mapping",
        "",
        "| Plugin class | Indicators |",
        "|---|---|",
    ]

    for plugin in plugins:
        indicators = plugin["indicators"]
        indicator_text = ", ".join(f"`{item}`" for item in indicators) if indicators else "(none)"
        lines.append(f"| `{plugin['class']}` | {indicator_text} |")

    lines.extend(
        [
            "",
            "## Plugin details",
            "",
            "| Plugin class | Version | ID | Source file | Requires |",
            "|---|---|---|---|---|",
        ]
    )

    for plugin in plugins:
        version = f"`{plugin['version']}`" if plugin["version"] else "-"
        plugin_id = f"`{plugin['id']}`" if plugin["id"] else "-"
        requires = plugin["requires"]
        requires_text = ", ".join(f"`{item}`" for item in requires) if requires else "-"
        lines.append(
            f"| `{plugin['class']}` | {version} | {plugin_id} | `{plugin['file']}` | {requires_text} |"
        )

    lines.extend(["", "## Indicator checks", "", W3ID_NOTE, ""])

    for plugin in plugins:
        indicators = plugin["indicators"]
        if not indicators:
            continue
        descriptions = plugin["descriptions"]
        lines.extend(
            [
                f"### {plugin['class']}",
                "",
                "| Indicator | What it checks | W3ID |",
                "|---|---|---|",
            ]
        )
        for indicator in indicators:
            description = descriptions.get(indicator)
            text = description.replace("|", "\\|") if description else "-"
            w3id = w3id_by_abbreviation.get(indicator)
            w3id_text = f"[`{indicator}`]({w3id})" if w3id else "-"
            lines.append(f"| `{indicator}` | {text} | {w3id_text} |")
        lines.append("")

    lines.append(INTERPRETING_RESULTS)
    lines.append("")
    lines.append(STATUS_IDS)

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    plugins = _extract_plugins()
    w3id_by_abbreviation = _fetch_w3id_by_abbreviation()
    markdown = _render_markdown(plugins, w3id_by_abbreviation)
    OUTPUT_FILE.write_text(markdown, encoding="utf-8")
    print(f"Generated {OUTPUT_FILE.relative_to(ROOT)} ({len(plugins)} plugins)")


if __name__ == "__main__":
    main()
