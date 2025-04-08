# reqsui

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
    resqui -c <config_file> <repository_url>

Options:
    <repository_url>  URL of the repository to be analyzed.
    -c <config_file>  Path to the configuration file.
    --version         Show the version of the script.
    --help            Show this help message.
```

## Configuration file

The preliminary configuration file format is JSON and consists a list
of indicators and the plugins to be used:

```json
{
  "indicators": [
	  { "name": "has_license", "plugin": "HowFairIs" },
	  { "name": "has_citation", "plugin": "CFFConvert" },
	  { "name": "has_security_leak", "plugin": "Gitleaks" }
  ]
}
```

## Example

```
$ resqui -c example.json https://github.com/JuliaHep/UnROOT.jl
  Checking indicator has_security_leak via Gitleaks: False
  Checking indicator has_license via HowFairIs: True
  Checking indicator has_citation via CFFConvert: True
```
