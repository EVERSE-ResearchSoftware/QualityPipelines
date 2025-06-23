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
	  { "name": "has_license", "plugin": "HowFairIs" },
	  { "name": "has_citation", "plugin": "CFFConvert" },
	  { "name": "has_ci_tests", "plugin": "OpenSSFScorecard" },
	  { "name": "human_code_review_requirement", "plugin": "OpenSSFScorecard" },
	  { "name": "has_published_package", "plugin": "OpenSSFScorecard" },
	  { "name": "has_no_security_leak", "plugin": "Gitleaks" }
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
    has_ci_tests/OpenSSFScorecard (6.2s): ✔
    human_code_review_requirement/OpenSSFScorecard (0.0s): ✖
    has_published_package/OpenSSFScorecard (0.0s): ✖
    has_no_security_leak/Gitleaks (0.4s): ✔
Summary has been written to resqui_summary.json
Publishing summary  ✖
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
