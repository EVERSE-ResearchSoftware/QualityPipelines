# Configuration Format

Configuration files are JSON documents that select which indicators to run
and which plugins to use for each.

## Schema

```json
{
  "indicators": [
    {
      "name": "<indicator_name>",
      "plugin": "<PluginClassName>",
      "@id": "<w3id_uri_or_missing>"
    }
  ]
}
```

### `name`

The method name on the plugin class that implements the check.
Must match exactly (case-sensitive).

### `plugin`

The class name of the plugin. Use `resqui indicators` to list all available
class names.

### `@id`

The W3ID URI that identifies this indicator in the EVERSE vocabulary.
Use the string `"missing"` if no URI has been assigned yet.

## Default configuration

When no `-c` flag is provided, resqui uses this built-in configuration:

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
    },
    {
      "name": "has_ci_tests",
      "plugin": "OpenSSFScorecard",
      "@id": "missing"
    },
    {
      "name": "human_code_review_requirement",
      "plugin": "OpenSSFScorecard",
      "@id": "missing"
    },
    {
      "name": "has_published_package",
      "plugin": "OpenSSFScorecard",
      "@id": "missing"
    },
    {
      "name": "has_no_security_leak",
      "plugin": "Gitleaks",
      "@id": "missing"
    }
  ]
}
```

## Example configurations

Ready-made configurations are included in the `configurations/` directory of
the repository and can be passed directly with `-c`.
