# Plugins & Indicators

This page is auto-generated from `src/resqui/plugins/` during docs build.

An **indicator** is a measurable property of a software repository. resqui maps
each indicator to a plugin method that performs the check automatically.

## Plugin to indicator mapping

| Plugin class | Indicators |
|---|---|
| `CFFConvert` | `has_citation` |
| `Gitleaks` | `has_no_security_leak` |
| `HowFairIs` | `has_license` |
| `OEBFAIR` | `unique_identifier`, `has_package`, `has_citation`, `has_license`, `has_documentation`, `has_releases`, `descriptive_metadata`, `listed_in_registry`, `versioning_standards_use`, `version_control_use`, `software_has_tests`, `repository_workflows`, `archived_in_software_heritage` |
| `OpenSSFScorecard` | `has_ci_tests`, `human_code_review_requirement`, `has_published_package`, `dependency_management`, `uses_fuzzing`, `no_critical_vulnerability`, `static_analysis_common_vulnerabilities`, `project_is_active`, `has_no_binary_artifacts`, `uses_tool_for_warnings_and_mistakes` |
| `RSFC` | `persistent_and_unique_identifier`, `requirements_specified`, `has_releases`, `software_has_citation`, `software_has_license`, `software_has_documentation`, `descriptive_metadata`, `versioning_standards_use`, `version_control_use`, `has_active_contributors`, `support_issue_tracking`, `codemeta_completeness`, `software_has_tests`, `repository_workflows`, `archived_in_software_heritage`, `has_contribution_guidelines`, `software_is_containerized`, `archived_in_scholarly_repository`, `has_active_communication_channels` |
| `SuperLinter` | `has_no_linting_issues` |

## Plugin details

| Plugin class | Version | ID | Source file | Requires |
|---|---|---|---|---|
| `CFFConvert` | `2.0.0` | `https://w3id.org/everse/tools/cffconvert` | `cffconvert.py` | - |
| `Gitleaks` | `8.24.2` | `https://w3id.org/everse/tools/gitleaks` | `gitleaks.py` | `docker` |
| `HowFairIs` | `0.14.2` | `https://w3id.org/everse/tools/howfairis` | `howfairis.py` | `github_token` |
| `OEBFAIR` | `0.2.2` | `https://w3id.org/everse/tools/fairsoft-evaluator` | `oebfair.py` | `docker`, `github_token` |
| `OpenSSFScorecard` | `v5.4.0` | `https://github.com/ossf/scorecard` | `openssfscorecard.py` | `docker`, `github_token` |
| `RSFC` | `0.2.0` | `https://w3id.org/everse/tools/rsfc` | `rsfc.py` | `docker` |
| `SuperLinter` | `8.7.0` | `https://w3id.org/everse/tools/superlinter` | `superlinter.py` | `docker` |

## Indicator checks

Indicators are matched to the [EVERSE indicator vocabulary](https://everse.software/indicators/api/indicators.json)
by exact name. Some plugins use internal aliases or plugin-specific
extensions that don't match a vocabulary abbreviation exactly (for example
`has_license` vs. the vocabulary's `software_has_license`, or SonarQube's
`code_quality_grade`, which has no vocabulary equivalent) — these show `-` in
the W3ID column rather than a guessed link.

### CFFConvert

| Indicator | What it checks | W3ID |
|---|---|---|
| `has_citation` | Searches for a 'CITATION.cff' file in the repository root and validates its syntax. | - |

### Gitleaks

| Indicator | What it checks | W3ID |
|---|---|---|
| `has_no_security_leak` | Searches for security leaks in the full repository history. | - |

### HowFairIs

| Indicator | What it checks | W3ID |
|---|---|---|
| `has_license` | Searches for a file named 'LICENSE' or 'LICENSE.md' in the repository root. | - |

### OEBFAIR

| Indicator | What it checks | W3ID |
|---|---|---|
| `unique_identifier` | - | - |
| `has_package` | - | - |
| `has_citation` | - | - |
| `has_license` | - | - |
| `has_documentation` | - | - |
| `has_releases` | - | [`has_releases`](https://w3id.org/everse/i/indicators/has_releases) |
| `descriptive_metadata` | - | [`descriptive_metadata`](https://w3id.org/everse/i/indicators/descriptive_metadata) |
| `listed_in_registry` | - | [`listed_in_registry`](https://w3id.org/everse/i/indicators/listed_in_registry) |
| `versioning_standards_use` | - | [`versioning_standards_use`](https://w3id.org/everse/i/indicators/versioning_standards_use) |
| `version_control_use` | - | [`version_control_use`](https://w3id.org/everse/i/indicators/version_control_use) |
| `software_has_tests` | - | [`software_has_tests`](https://w3id.org/everse/i/indicators/software_has_tests) |
| `repository_workflows` | - | [`repository_workflows`](https://w3id.org/everse/i/indicators/repository_workflows) |
| `archived_in_software_heritage` | - | [`archived_in_software_heritage`](https://w3id.org/everse/i/indicators/archived_in_software_heritage) |

### OpenSSFScorecard

| Indicator | What it checks | W3ID |
|---|---|---|
| `has_ci_tests` | Checks if there are PRs checked by CI-Tests | - |
| `human_code_review_requirement` | Checks if at least half of the changesets in the repository are approved | [`human_code_review_requirement`](https://w3id.org/everse/i/indicators/human_code_review_requirement) |
| `has_published_package` | Checks if there are workflows for package releasing (i.e PyPI) | [`has_published_package`](https://w3id.org/everse/i/indicators/has_published_package) |
| `dependency_management` | Checks if there is a dependency update tool in the repository | [`dependency_management`](https://w3id.org/everse/i/indicators/dependency_management) |
| `uses_fuzzing` | Checks if the project integrates fuzzing | [`uses_fuzzing`](https://w3id.org/everse/i/indicators/uses_fuzzing) |
| `no_critical_vulnerability` | Checks if there are vulnerabilities in the repository | [`no_critical_vulnerability`](https://w3id.org/everse/i/indicators/no_critical_vulnerability) |
| `static_analysis_common_vulnerabilities` | Checks if there are commits checked with a SAST tool | [`static_analysis_common_vulnerabilities`](https://w3id.org/everse/i/indicators/static_analysis_common_vulnerabilities) |
| `project_is_active` | Checks if there are commits and issue activity in the last 90 days | [`project_is_active`](https://w3id.org/everse/i/indicators/project_is_active) |
| `has_no_binary_artifacts` | Checks if the project contains binary artifacts | [`has_no_binary_artifacts`](https://w3id.org/everse/i/indicators/has_no_binary_artifacts) |
| `uses_tool_for_warnings_and_mistakes` | Checks whether the project uses a static analysis tool to detect code quality errors or common mistakes. A low Scorecard Static Application Security Testing (SAST) score does not necessarily mean that the project does not use SAST, since Scorecard may not detect all possible SAST setups. Documentation: https://github.com/ossf/scorecard/blob/main/docs/checks.md#sast | [`uses_tool_for_warnings_and_mistakes`](https://w3id.org/everse/i/indicators/uses_tool_for_warnings_and_mistakes) |

### RSFC

| Indicator | What it checks | W3ID |
|---|---|---|
| `persistent_and_unique_identifier` | - | [`persistent_and_unique_identifier`](https://w3id.org/everse/i/indicators/persistent_and_unique_identifier) |
| `requirements_specified` | - | [`requirements_specified`](https://w3id.org/everse/i/indicators/requirements_specified) |
| `has_releases` | - | [`has_releases`](https://w3id.org/everse/i/indicators/has_releases) |
| `software_has_citation` | - | [`software_has_citation`](https://w3id.org/everse/i/indicators/software_has_citation) |
| `software_has_license` | - | [`software_has_license`](https://w3id.org/everse/i/indicators/software_has_license) |
| `software_has_documentation` | - | [`software_has_documentation`](https://w3id.org/everse/i/indicators/software_has_documentation) |
| `descriptive_metadata` | - | [`descriptive_metadata`](https://w3id.org/everse/i/indicators/descriptive_metadata) |
| `versioning_standards_use` | - | [`versioning_standards_use`](https://w3id.org/everse/i/indicators/versioning_standards_use) |
| `version_control_use` | - | [`version_control_use`](https://w3id.org/everse/i/indicators/version_control_use) |
| `has_active_contributors` | - | [`has_active_contributors`](https://w3id.org/everse/i/indicators/has_active_contributors) |
| `support_issue_tracking` | - | [`support_issue_tracking`](https://w3id.org/everse/i/indicators/support_issue_tracking) |
| `codemeta_completeness` | - | [`codemeta_completeness`](https://w3id.org/everse/i/indicators/codemeta_completeness) |
| `software_has_tests` | - | [`software_has_tests`](https://w3id.org/everse/i/indicators/software_has_tests) |
| `repository_workflows` | - | [`repository_workflows`](https://w3id.org/everse/i/indicators/repository_workflows) |
| `archived_in_software_heritage` | - | [`archived_in_software_heritage`](https://w3id.org/everse/i/indicators/archived_in_software_heritage) |
| `has_contribution_guidelines` | - | [`has_contribution_guidelines`](https://w3id.org/everse/i/indicators/has_contribution_guidelines) |
| `software_is_containerized` | - | [`software_is_containerized`](https://w3id.org/everse/i/indicators/software_is_containerized) |
| `archived_in_scholarly_repository` | - | [`archived_in_scholarly_repository`](https://w3id.org/everse/i/indicators/archived_in_scholarly_repository) |
| `has_active_communication_channels` | - | [`has_active_communication_channels`](https://w3id.org/everse/i/indicators/has_active_communication_channels) |

### SuperLinter

| Indicator | What it checks | W3ID |
|---|---|---|
| `has_no_linting_issues` | Searches for linting errors. | [`has_no_linting_issues`](https://w3id.org/everse/i/indicators/has_no_linting_issues) |

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
