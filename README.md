# resqui

A command line tool to check a bunch of indicators related to research software
quality.

## Installation

Preferably inside a Python virtual environment:

```
pip install .
```

## Usage

```
$ resqui -h
Usage:
    resqui [options] -c <config_file> <repository_url>

Options:
    <repository_url>  URL of the repository to be analyzed.
    -c <config_file>  Path to the configuration file.
    -b <branch>       The Git branch to be checked [default: main].
    --version         Show the version of the script.
    --help            Show this help message.
```

### Configuration file

The preliminary configuration file format is JSON and consists a list
of indicators and the plugins to be used. The `name` field matches the
actual method of the class named `plugin`:

```json
{
  "indicators": [
	  { "name": "has_license", "plugin": "HowFairIs", "@id": "https://w3id.org/everse/i/indicators/license" },
	  { "name": "has_citation", "plugin": "CFFConvert", "@id": "https://w3id.org/everse/i/indicators/citation" }
  ]
}
```


### Example

```
$ resqui -c example.json -t *** https://github.com/EVERSE-ResearchSoftware/QualityPipelines
GitHub API token ✔
Repository URL: https://github.com/EVERSE-ResearchSoftware/QualityPipelines
Branch: main
Checking indicators ...
    has_license/HowFairIs (0.4s): ✔
    has_citation/CFFConvert (0.2s): ✖
Summary has been written to resqui_summary.json
Publishing summary  ✖
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
