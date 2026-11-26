#!/usr/bin/env python3
"""Check that configs point to real indicators and that declared
indicators are configured somewhere. Standard library only."""

import ast
import difflib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "configurations"
PLUGINS_DIR = ROOT / "src" / "resqui" / "plugins"
CONFIG_PY = ROOT / "src" / "resqui" / "config.py"


def literal_value(node):
    """Return the literal value of a simple assignment, if possible."""
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None


def load_plugins():
    """Collect the exported plugin classes, their methods and indicators."""
    exported = set()
    init_file = PLUGINS_DIR / "__init__.py"
    for node in ast.parse(init_file.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.ImportFrom):
            exported.update(alias.name for alias in node.names)

    plugins = {}
    for path in sorted(PLUGINS_DIR.glob("*.py")):
        if path.name in ("__init__.py", "base.py"):
            continue
        for cls in ast.parse(path.read_text(encoding="utf-8")).body:
            if not isinstance(cls, ast.ClassDef):
                continue
            methods = {
                n.name
                for n in cls.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            declared = []
            for node in cls.body:
                if not isinstance(node, ast.Assign):
                    continue
                if not any(getattr(t, "id", None) == "indicators" for t in node.targets):
                    continue
                value = literal_value(node.value)
                if isinstance(value, (list, tuple)):
                    declared = list(value)
            plugins[cls.name] = {
                "methods": methods,
                "declared": declared,
                "exported": cls.name in exported,
            }
    return plugins


def load_configs():
    """Load every JSON config plus the built-in DEFAULT_CONFIG."""
    configs = []
    for path in sorted(CONFIG_DIR.rglob("*.json")):
        label = str(path.relative_to(ROOT))
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            configs.append((label, [], "Invalid JSON: %s" % error))
            continue
        indicators = data.get("indicators", []) if isinstance(data, dict) else []
        configs.append((label, indicators, None))

    for node in ast.parse(CONFIG_PY.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(
            getattr(t, "id", None) == "DEFAULT_CONFIG" for t in node.targets
        ):
            value = literal_value(node.value)
            if isinstance(value, dict):
                configs.append(
                    (
                        "src/resqui/config.py::DEFAULT_CONFIG",
                        value.get("indicators", []),
                        None,
                    )
                )
    return configs


def check(configs, plugins):
    """Collect all inconsistencies in both directions."""
    errors = []
    covered = set()

    # Config -> code: plugin and method must exist.
    for label, indicators, parse_error in configs:
        if parse_error:
            errors.append((label, "-", "-", parse_error))
            continue
        for position, entry in enumerate(indicators):
            if not isinstance(entry, dict):
                errors.append((label, "-", "-", "entry %d is not an object" % position))
                continue
            plugin = entry.get("plugin")
            name = entry.get("name")
            if plugin not in plugins or not plugins[plugin]["exported"]:
                errors.append((label, plugin, name, "plugin does not exist or is not exported"))
                continue
            if name not in plugins[plugin]["methods"]:
                hint = difflib.get_close_matches(
                    str(name), plugins[plugin]["declared"], n=1, cutoff=0.6
                )
                reason = "indicator is not a method of the plugin"
                if hint:
                    reason += " (did you mean %s?)" % hint[0]
                errors.append((label, plugin, name, reason))
                continue
            covered.add((plugin, name))
    # Code -> config: every declared indicator must be configured somewhere.
    for plugin in sorted(plugins):
        for name in plugins[plugin]["declared"]:
            if (plugin, name) not in covered:
                errors.append(
                    ("(no config)", plugin, name, "declared indicator has no configuration")
                )
    return errors


def main():
    plugins = load_plugins()
    configs = load_configs()
    errors = check(configs, plugins)

    print("Configurations checked: %d" % len(configs))
    print("Plugins found: %d" % len(plugins))
    print("")
    if not errors:
        print("OK: no inconsistencies found.")
        return 0

    print("INCONSISTENCIES (%d):" % len(errors))
    for label, plugin, name, reason in errors:
        print("  %s | %s/%s | %s" % (label, plugin, name, reason))
    return 1


if __name__ == "__main__":
    sys.exit(main())