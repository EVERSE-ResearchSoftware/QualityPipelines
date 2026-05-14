# EVERSE Software Quality Pipelines

The EVERSE Software Quality Pipelines provide

1) the command line tool `resqui` to check a configurable set of software quality indicators on research software via external plugins (tools); 
2) GitHub Action to run the pipeline on a github repository.

## Documentation

### Quality Pipelines

1) `resqui`
`resqui` is installed - preferable within a Python virtual environment - as follows:

```
git clone https://github.com/EVERSE-ResearchSoftware/QualityPipelines.git
cd QualityPipelines
pip install .
```
and can be executed with these options:

```
$ resqui -h
Usage:
    resqui [options]
    resqui indicators

Options:
    -u <repository_url>   URL of the repository to be analyzed.
    -c <config_file>      Path to the configuration file.
    -o <output_file>      Path to the output file [default: resqui_summary.json].
    -t <github_token>     GitHub API token.
    -d <dashverse_token>  DashVerse API token.
    -b <branch>           The Git branch to be checked.
    -v                    Verbose output.
    --version             Show the version of the script.
    --help                Show this help message.
 ```
The complete documentation of the quality pipelines are available at the project's [Github Pages](https://everse.software/QualityPipelines/);

2) The GitHub Action to include in CI/CDs pipeline is available in [this repository](https://github.com/EVERSE-ResearchSoftware/resqui-github-action).

### EVERSE Services

EVERSE provides a set of services to assess and improve the quality of research software, visit the [EVERSE homepage](https://everse.software) for more information.

A simplified workflow to improve the software quality is: 
Find the practices on `RSQKit` (1), get an overview on tools and services to measure and improve the quality on the `TechRadar` (2), run an assessment on your own or your groups software via resqui (3) and display the results on `DashVERSE` (4), assess and repeat from (1).

More information the services can be found at:

1) Research Software Quality Kit - [RSQKit](https://everse.software/services/rsqkit/)
2) Technology Radar - [TechRadar](https://everse.software/services/techradar/)
3) Quality Pipelines - `resqui` which is this project
4) Software Quality Dashboards - [DashVERSE](https://everse.software/services/dashverse/)

