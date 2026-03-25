# Indicators

An **indicator** is a measurable property of a software repository. resqui maps
each indicator to a plugin method that performs the check automatically.

## Built-in indicators

### `has_license` — HowFairIs

Looks for a file named `LICENSE` or `LICENSE.md` in the repository root using
the [howfairis](https://github.com/fair-software/howfairis) library. Requires a
GitHub token.

W3ID: `https://w3id.org/everse/i/indicators/license`

### `has_citation` — CFFConvert

Checks for a valid `CITATION.cff` file using
[cffconvert](https://github.com/citation-file-format/cffconvert). Both
presence and schema validity are verified.

W3ID: `https://w3id.org/everse/i/indicators/citation`

### `has_ci_tests` — OpenSSFScorecard

Checks whether the project has a functioning CI test setup, as determined by
the [OpenSSF Scorecard](https://github.com/ossf/scorecard). Runs via Docker.
Requires a GitHub token.

### `human_code_review_requirement` — OpenSSFScorecard

Checks whether pull requests require human review before merging, per the
OpenSSF Scorecard "Code-Review" check.

### `has_published_package` — OpenSSFScorecard

Checks whether the project publishes a package to a registry such as PyPI or
npm, per the OpenSSF Scorecard "Packaging" check.

### `has_no_security_leak` — Gitleaks

Scans the repository history for accidentally committed secrets (API keys,
tokens, passwords) using [Gitleaks](https://github.com/gitleaks/gitleaks).
Runs via Docker.

## Interpreting results

Each indicator produces a `CheckResult` with:

| Field | Values |
|---|---|
| `output` | `valid` — indicator satisfied; `missing` — not found; `failed` — check error |
| `status` | Schema.org action status IRI |
| `evidence` | Human-readable finding from the underlying tool |

An indicator returning `missing` or `failed` does **not** abort the run — all
configured indicators are always attempted.

## Status IDs

| Status IRI | Meaning |
|---|---|
| `schema:CompletedActionStatus` | Check passed |
| `schema:FailedActionStatus` | Check ran but found a problem |
| `missing` | Check could not be completed (plugin skipped) |
