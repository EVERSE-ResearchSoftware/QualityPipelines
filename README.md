# resqui

A command line tool to check a bunch of indicators related to research software
quality.

## Installation

Preferably inside a Python virtual environment:

```
git clone https://github.com/EVERSE-ResearchSoftware/QualityPipelines.git
cd QualityPipelines
pip install .
```

## Usage

```
$ resqui -h
Usage:
    resqui [options]
    resqui indicators

Options:
    -u <repository_url>  URL of the repository to be analyzed.
    -c <config_file>     Path to the configuration file.
    -o <output_file>     Path to the output file [default: resqui_summary.json].
    -t <github_token>    GitHub API token.
    -b <branch>          The Git branch to be checked.
    -v                   Verbose output.
    --version            Show the version of the script.
    --help               Show this help message.
```

### Configuration file (optional)

The preliminary configuration file format is JSON and consists a list
of indicators and the plugins to be used. The `name` field matches the
actual method of the class named `plugin`. If no configuration file is
provided, a default set of indicators will be used.

```json
{
  "indicators": [
	  { "name": "has_license", "plugin": "HowFairIs", "@id": "https://w3id.org/everse/i/indicators/license" },
	  { "name": "has_citation", "plugin": "CFFConvert", "@id": "https://w3id.org/everse/i/indicators/citation" }
  ]
}
```

## GitHub Action

**resqui** offers a GitHub action which can be installed by creating a dedicated
configuration file in the `.github/workflows` folder, named e.g. `resqui.yml`
with the content below. It also needs a new **environment** called **resqui** in
your GitHub repository settings under
`https://github.com/USER_OR_GROUP/PROJECT/settings/environments` with a secret
environment variable named `DASHVERSE_TOKEN` which is needed for publishing the
pipeline results to the DashVerse instance.

Note: the CI action will be triggered on each "push". Make sure to **Allow all
actions and reusable workflows** in the repository settings under
`https://github.com/USER_OR_GROUP/PROJECT/settings/actions`.

### `.github/workflows/resqui.yml` Example

``` yaml
name: Run Resqui CI

on:
  push:

jobs:
  run-resqui:
    runs-on: ubuntu-latest
    # make sure to match the environment's name
    environment: resqui

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run resqui action
        uses: EVERSE-ResearchSoftware/QualityPipelines@main
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          dashverse_token: ${{ secrets.DASHVERSE_TOKEN }}
          # a configuartion file is optional and can be placed at the root of the repository
          # config: .resqui.json
```



### Command line tool: `resqui`

The `resqui` command line tool can be used to generate and publish a report.
Some indicator plugins require a GitHub API access token, which can be passed via `-t`.
A personal access token is can be generated on the GitHub
website: https://github.com/settings/personal-access-tokens
Be aware that some GitHub organisations might disallow tokens with no expiration date.
When running `resqui` as a GitHub action, the automatically generated token from the CI
job will be used.

```
$ resqui -c example.json -t $RESQUI_GITHUB_TOKEN
GitHub API token ✔
Repository URL: https://github.com/EVERSE-ResearchSoftware/QualityPipelines.git
Project name: QualityPipelines
Author: Tamas Gal
Email: himself@tamasgal.com
Version: v0.1.0-95-gc1dacb1
Branch, tag or commit hash: c1dacb1197005e9bce20063b2215bdfd7f9939d9
Checking indicators ...
    has_license/HowFairIs (1.2s): ✖
    has_citation/CFFConvert (1.0s): ✖
Summary has been written to resqui_summary.json
Publishing summary  ✔
```

### Output File

The current output format is a `JSON`, based on the Schema presented here: https://github.com/EVERSE-ResearchSoftware/schemas/blob/main/assessment/dev/example.json

```json
{
    "@context": "https://w3id.org/everse/rsqa/0.0.1/",
    "@type": "SoftwareQualityAssessment",
    "dateCreated": "2025-07-16 09:17:34.280112",
    "license": {
        "@id": "https://creativecommons.org/publicdomain/zero/1.0/"
    },
    "checks": [
        {
            "@type": "CheckResult",
            "assessesIndicator": {
                "@id": "https://w3id.org/everse/i/indicators/license"
            },
            "checkingSoftware": {
                "@type": "schema:SoftwareApplication",
                "name": "HowFairIs",
                "@id": "https://w3id.org/everse/tools/howfairis",
                "softwareVersion": "0.14.2"
            },
            "process": "Searches for a file named 'LICENSE' or 'LICENSE.md' in the repository root.",
            "status": {
                "@id": "schema:CompletedActionStatus"
            },
            "output": "valid",
            "evidence": "Found license file: 'LICENSE'."
        },
        {
            "@type": "CheckResult",
            "assessesIndicator": {
                "@id": "https://w3id.org/everse/i/indicators/citation"
            },
            "checkingSoftware": {
                "@type": "schema:SoftwareApplication",
                "name": "CFFConvert",
                "@id": "https://w3id.org/everse/tools/cffconvert",
                "softwareVersion": "2.0.0"
            },
            "process": "Searches for a 'CITATION.cff' file in the repository root and validates its syntax.",
            "status": {
                "@id": "schema:CompletedActionStatus"
            },
            "output": "invalid",
            "evidence": "No valid CITATION.cff file found in repository root."
        }
    ]
}
```
## Indicator Plugins

An indicator plugin is represented by a subclass of
`resqui.plugins.IndicatorPlugin` and uses either a
`resqui.plugins.PythonExecutor` or a `resqui.plugins.DockerExecutor` to run the
software to determine the indicator values.
The subclassing is mainly used to identify plugins during runtime,
there is no other inheritence magic behind that.

Each indicator is implemented as a member function with the same name (e.g. `has_license`).
The method should return an instance of `CheckResult` or a list of those.

### Mandatory Attributes

Each indicator plugin should define a set of class attributes:

- `name`: currently matches the class name
- `version`: dot-separated numbers
- `id`: URL of the tool description on w3id.org
- `indicators`: a list of indicators, matching the actual method names

### Executors

#### `PythonExecutor`

The Python executor manages a virtual environment and installs the required
packages via `pip`. A script can be passed to `.execute()` which returns the
result as an instance of `subprocess.CompletedProcess` that is executed inside
the virtual environment.

#### `DockerExecutor`

The Docker executor pulls the required image and allows to run scripts inside a
container spawned from that very image. The command is passed to `.run()` with
optional argments that are passed to the `docker run` command. The result is
returned similar to the `PythonExecutor` as an instance of
`subprocess.CompletedProcess`.
