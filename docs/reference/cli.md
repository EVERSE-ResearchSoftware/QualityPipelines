# CLI Reference

## Synopsis

```
resqui [options]
resqui indicators
```

## Options

| Flag | Argument | Default | Description |
|---|---|---|---|
| `-u` | `<repository_url>` | current repo | URL of the repository to assess. If omitted, resqui reads the remote repository URL from the current working directory's `.git` metadata. |
| `-c` | `<config_file>` | built-in default | Path to a JSON configuration file. |
| `-o` | `<output_file>` | `resqui_summary.json` | Path for the JSON-LD output report. |
| `--md` | `<markdown_report>` | — | Path for a Markdown report, generated from the JSON output after the assessment completes. |
| `-t` | `<github_token>` | — | GitHub personal access token. Required by `HowFairIs` and `OpenSSFScorecard`. |
| `-d` | `<dashverse_token>` | — | DashVerse API token. When provided, the summary is uploaded after assessment. |
| `-b` | `<branch>` | HEAD commit | Git branch, tag, or commit hash to assess. |
| `-v` | — | off | Verbose output: prints full evidence text for each indicator. |
| `--version` | — | — | Print the installed version and exit. |
| `--help` | — | — | Print usage and exit. |

## Subcommands

### `indicators`

```bash
resqui indicators
```

Prints all available plugin classes, their versions, and the indicator names
they expose. Useful for discovering what can go into a configuration file.

## Markdown reports

Besides `--md`, which generates a Markdown report at the end of a `resqui`
run, an existing JSON report can be converted on its own with the
`resqui.markdown_report` module — no re-run of the assessment needed:

```bash
python -m resqui.markdown_report resqui_summary.json -o resqui_summary.md
```

This works from any `resqui` install (including from PyPI), since it only
needs the module to be importable, not a registered console script.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Assessment completed (individual indicator failures do not affect the exit code) |
| `1` | Fatal error (not a Git repository, clone failed, etc.) |
