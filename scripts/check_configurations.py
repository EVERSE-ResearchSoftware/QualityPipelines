#!/usr/bin/env python3
"""Check that configs point to real plugin indicators and that every
declared indicator appears in configurations/complete.json."""

import difflib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import resqui.plugins as plugins_module
from resqui.config import DEFAULT_CONFIG

CONFIG_DIR = ROOT / "configurations"
COMPLETE_LABEL = "configurations/complete.json"
SKIP = {"IndicatorPlugin", "PluginInitError"}
KEYS = ("plugin", "name", "@id")


def load_plugins():
    """Return the exported plugin classes, as the runtime sees them."""
    result = {}
    for name in plugins_module.__all__:
        if name in SKIP:
            continue
        cls = getattr(plugins_module, name, None)
        if isinstance(cls, type):
            result[name] = cls
    return result


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

    configs.append(
        (
            "src/resqui/config.py::DEFAULT_CONFIG",
            DEFAULT_CONFIG.get("indicators", []),
            None,
        )
    )

    return configs


def check(configs, plugins):
    """Collect all inconsistencies in both directions."""
    errors = []
    covered = set()

    # Reference set: only complete.json defines which indicators must exist.
    for label, indicators, parse_error in configs:
        if label == COMPLETE_LABEL and not parse_error:
            covered = {
                (entry["plugin"], entry["name"])
                for entry in indicators
                if isinstance(entry, dict) and "plugin" in entry and "name" in entry
                }

    for label, indicators, parse_error in configs:
        if parse_error:
            errors.append((label, "-", "-", parse_error))
            continue
        for position, entry in enumerate(indicators):
            if not isinstance(entry, dict):
                errors.append((label, "-", "-", "entry %d is not an object" % position))
                continue
            missing = [key for key in KEYS if key not in entry]
            if missing:
                errors.append(
                    (label, "-", "-", "missing key(s): %s" % ", ".join(missing))
                )
                continue

            plugin_name, name = entry["plugin"], entry["name"]
            cls = plugins.get(plugin_name)
            if cls is None:
                errors.append(
                    (label, plugin_name, name, "plugin is not exported by resqui.plugins")
                )
                continue
            declared = list(getattr(cls, "indicators", []) or [])
            if name not in declared or not hasattr(cls, name):
                hint = difflib.get_close_matches(str(name), declared, n=1, cutoff=0.6)
                reason = "indicator is not declared and implemented by the plugin"
                if hint:
                    reason += " (did you mean %s?)" % hint[0]
                errors.append((label, plugin_name, name, reason))

    # Code -> config: only exported plugins, checked against complete.json.
    for plugin_name, cls in sorted(plugins.items()):
        for name in getattr(cls, "indicators", []) or []:
            if (plugin_name, name) not in covered:
                errors.append(
                    (
                        COMPLETE_LABEL,
                        plugin_name,
                        name,
                        "declared indicator is missing from complete.json",
                    )
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