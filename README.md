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

## Configuration file

The preliminary configuration file format is JSON and consists a list
of indicators and the plugins to be used:

```json
{
  "api_endpoint": "https://everse.software/api/v1",
  "indicators": [
	  { "name": "has_license", "plugin": "HowFairIs" },
	  { "name": "has_citation", "plugin": "CFFConvert" },
	  { "name": "has_no_linting_issues", "plugin": "SuperLinter" },
	  { "name": "has_security_leak", "plugin": "Gitleaks" }
  ]
}
```

## Example

```
$ resqui -c example.json https://github.com/JuliaHep/UnROOT.jl
Repository URL: https://github.com/JuliaHep/UnROOT.jl
Branch: main
Checking indicators ...
    has_license/HowFairIs (4.1s): ✔
    has_citation/CFFConvert (3.4s): ✔
    has_no_linting_issues/SuperLinter (125.7s): ✖
    has_security_leak/Gitleaks (63.7s): ✔
Summary has been written to resqui_summary.json
Publishing summary  ✖
```
