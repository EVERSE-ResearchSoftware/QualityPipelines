# resqui

**resqui** is a command-line tool that checks research software quality indicators.
It analyses a Git repository against a configurable set of indicators and produces
a [JSON-LD](https://json-ld.org/) assessment report conforming to the
[EVERSE Research Software Quality Assessment schema](https://github.com/EVERSE-ResearchSoftware/schemas).

## Requirements

- Python 3.9+
- Docker (required by several indicator plugins)

## Installation

```bash
pip install resqui
```

## Quick start

Run against the current repository using the default indicator set:

```bash
resqui -t $GITHUB_TOKEN
```

Run against a remote repository and write output to a custom file:

```bash
resqui -u https://github.com/org/repo -t $GITHUB_TOKEN -o report.json
```

## Navigation

| Section | What you'll find |
|---|---|
| **Tutorials** | Step-by-step lessons — start here if you're new |
| **How-to guides** | Recipes for specific tasks (custom configs, adding plugins, CI setup) |
| **Reference** | Complete CLI, configuration, and API documentation |
| **Explanation** | Architecture decisions and indicator background |
