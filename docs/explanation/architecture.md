# Architecture

## Overview

resqui is built around three concepts: **plugins**, **executors**, and a
**configuration-driven pipeline**. The CLI wires them together but the
components are independent.

```
CLI (cli.py)
 │
 ├─ Configuration (config.py)      ← JSON file or built-in defaults
 │
 ├─ GitInspector (cli.py)          ← extracts metadata from the repo
 │
 ├─ IndicatorPlugin subclasses     ← one per tool (HowFairIs, Gitleaks, …)
 │    └─ uses Executor             ← PythonExecutor or DockerExecutor
 │
 └─ Summary (core.py)              ← aggregates CheckResults → JSON-LD
```

## Plugin system

Every quality check is a subclass of `IndicatorPlugin`. The CLI discovers
plugins at runtime via `__subclasses__()` — no registration step is needed.
Each plugin declares a list of indicator names in its `indicators` class
attribute; each name corresponds to a method of the same name on the class.

A single plugin instance is reused for all of its indicators within one run,
which means Docker images are pulled and Python venvs are created only once
per plugin class.

## Executor design

Plugins delegate subprocess execution to one of two executors:

**`PythonExecutor`** creates a temporary `venv` via the stdlib `venv` module,
installs the required packages with pip, and runs Python snippets inside it.
The venv is torn down in `__del__`. This approach keeps plugin dependencies
completely isolated from the resqui installation.

**`DockerExecutor`** pulls a Docker image on construction and runs commands
inside containers via `docker run`. The Docker daemon is the only external
dependency.

Both raise `ExecutorInitError` when they cannot initialise (Docker unavailable,
pip install failure, etc.). The CLI catches this and skips all indicators
belonging to that plugin with a warning, allowing the rest of the run to
continue.

## Why not extend IndicatorPlugin with Python magic?

Subclassing is used purely as a discovery mechanism — `__subclasses__()` gives
a flat list of all available plugins without any import-side-effect registration.
There is no `__init_subclass__` hook or metaclass. This keeps plugin authorship
simple: write a class, import it, and it is automatically available.

## Output format

`Summary.to_json()` serialises results as JSON-LD conforming to the EVERSE
Research Software Quality Assessment schema
(`https://w3id.org/everse/rsqa/0.0.1/`). Each `CheckResult` maps to one entry
in the `checks` array with linked indicator, software, and status IRIs.
