# CLI Reference

## Synopsis

```
resqui [options]
resqui indicators
```

## Options

| Flag | Argument | Default | Description |
|---|---|---|---|
| `-u` | `<repository_url>` | current repo | URL of the repository to assess. If omitted, resqui uses the remote URL of the current working directory. |
| `-c` | `<config_file>` | built-in default | Path to a JSON configuration file. |
| `-o` | `<output_file>` | `resqui_summary.json` | Path for the JSON-LD output report. |
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

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Assessment completed (individual indicator failures do not affect the exit code) |
| `1` | Fatal error (not a Git repository, clone failed, etc.) |
