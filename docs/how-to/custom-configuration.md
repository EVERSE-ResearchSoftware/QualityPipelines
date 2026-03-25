# Write a Custom Configuration

By default resqui runs the built-in indicator set. A JSON configuration file
lets you choose exactly which indicators to run and which plugins to use.

## Configuration file format

```json
{
  "indicators": [
    {
      "name": "has_license",
      "plugin": "HowFairIs",
      "@id": "https://w3id.org/everse/i/indicators/license"
    },
    {
      "name": "has_citation",
      "plugin": "CFFConvert",
      "@id": "https://w3id.org/everse/i/indicators/citation"
    }
  ]
}
```

| Field | Description |
|---|---|
| `name` | Must match a method name on the plugin class |
| `plugin` | Class name of the plugin (see `resqui indicators`) |
| `@id` | W3ID URI for the indicator (use `"missing"` if no URI exists yet) |

## Using a custom config

Pass the file with `-c`:

```bash
resqui -c my-config.json -t $GITHUB_TOKEN
```

## Example configurations

The `configurations/` directory in the repository contains ready-made configs
for different use cases:

| File | Purpose |
|---|---|
| `basic.json` | License and citation only |
| `indicators_analysis_code.json` | Indicators for analysis code |
| `indicators_prototype_tools.json` | Indicators for prototype tools |
| `indicators_rs_infrastructure.json` | Indicators for RS infrastructure |

## Discovering available plugins and indicators

```bash
resqui indicators
```

This prints every plugin class, its version, and the indicator names it supports.
