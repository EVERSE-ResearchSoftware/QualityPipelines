# Your First Assessment

This tutorial walks you through running your first quality assessment from scratch.
By the end you will have a signed JSON-LD report listing the quality indicators
for a real repository.

## Prerequisites

- Python 3.9+ installed
- Docker running (needed by most plugins)
- A GitHub personal access token (read-only scope is enough)

You can create a token at <https://github.com/settings/personal-access-tokens>.

## 1. Install resqui

Create a virtual environment and install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install resqui
```

## 2. Check your current repository

Navigate to any Git repository on your machine and run:

```bash
resqui -t $GITHUB_TOKEN
```

resqui detects the remote URL automatically and runs all default indicators.
You will see a live progress line per indicator:

```
Loading default configuration.
GitHub API token ✔
Repository URL: https://github.com/org/myproject.git
Project name: myproject
Author: Your Name
Version: v1.2.0
Checking indicators ...
  has_license/HowFairIs (0.9s): ✔
  has_citation/CFFConvert (0.3s): ✔
  has_ci_tests/OpenSSFScorecard (12.4s): ✔
  ...
Summary has been written to resqui_summary.json
```

## 3. Inspect the report

Open `resqui_summary.json`. Each entry in `checks` corresponds to one indicator:

```json
{
  "@type": "CheckResult",
  "assessesIndicator": { "@id": "https://w3id.org/everse/i/indicators/license" },
  "checkingSoftware": { "name": "HowFairIs", "version": "0.14.2" },
  "evidence": "Found license file: 'LICENSE'.",
  "output": "valid",
  "status": { "@id": "schema:CompletedActionStatus" }
}
```

- **evidence** – the human-readable finding from the plugin
- **output** – `valid`, `missing`, or `failed`
- **status** – linked schema.org action status

## 4. Check a remote repository

You can point resqui at any public repository without cloning it yourself:

```bash
resqui -u https://github.com/org/other-project -t $GITHUB_TOKEN -o other-report.json
```

## Next steps

- [Write a custom configuration](../how-to/custom-configuration.md) to choose which indicators to run
- [Integrate resqui in GitHub Actions](../how-to/ci-integration.md) to run it automatically on every push
