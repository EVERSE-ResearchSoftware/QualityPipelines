# Software Management Plan indicator profiles — v3 (reconciled)

Source: [Practical guide to Software Management Plans](https://zenodo.org/records/7589725) (Netherlands eScience Center / NWO).

The Practical guide to SMP provides a list of core requirements for research software, divided into 3 categories (low, medium, high).

Here, we map the EVERSE indicators to these core requirements and provide the corresponding configurations.

Last update: 2026-07-17.   
Author: Thomas Vuillaume

## 1. Management levels (corrected)

This is Table 4 of the guide, corrected for the three missing practices (User documentation, Software licensing and compatibility, and Deployment documentation) at low level (see Table 1 of the same document).


| Core requirement (Section 5.1)       | Low (6.1.1) | Medium (6.1.2) | High (6.1.3) |
|--------------------------------------|:-----------:|:--------------:|:------------:|
| Purpose                              |      X      |       X        |      X       |
| Version control                      |      X      |       X        |      X       |
| Repository                           |             |       X        |      X       |
| User documentation                   |      X      |       X        |      X       |
| Software licensing and compatibility |      X      |       X        |      X       |
| Deployment documentation             |      X      |       X        |      X       |
| Citation                             |             |       X        |      X       |
| Developer documentation              |             |       X        |      X       |
| Testing                              |             |       X        |      X       |
| Software Engineering quality         |             |       X        |      X       |
| Packaging                            |             |       X        |      X       |
| Maintenance                          |             |       X        |      X       |
| Support                              |             |                |      X       |
| Risk analysis                        |             |                |      X       |


## 2. Indicator mapping 

Two columns, deliberately not one bucket:

- **Validates** — if this indicator passes, the core requirement is met. One per row, chosen as the strongest single sufficient proxy.
- **Participates in validation** — contributes evidence but isn't independently sufficient (partial coverage, a maturity add-on, or one of several alternative routes to the same outcome).

| Core requirement                     | Validates without ambiguity              | Tool (wired up in this repo) | Participates in validation                                                                                                                                                                                                   |
|--------------------------------------|------------------------------------------|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose                              | `descriptive_metadata`                   | OEBFAIR, RSFC                | `codemeta_completeness`, `metadata_is_up_to_date`                                                                                                                                                                            |
| Version control                      | `version_control_use`                    | RSFC                         | `versioning_standards_use`                                                                                                                                                                                                   |
| Repository                           | `persistent_and_unique_identifier`       | OEBFAIR, RSFC                | `archived_in_scholarly_repository`, `archived_in_software_heritage`, `listed_in_registry`                                                                                                                                    |
| User documentation                   | `software_has_documentation`             | OEBFAIR, RSFC                | —                                                                                                                                                                                                                            |
| Software licensing and compatibility | `software_has_license`                   | HowFairIs, OEBFAIR, RSFC     | `software_has_license_for_file_types`                                                                                                                                                                                        |
| Deployment documentation             | `requirements_specified`                 | RSFC                         | `dependency_management`                                                                                                                                                                                                      |
| Citation                             | `software_has_citation`                  | CFFConvert, OEBFAIR, RSFC    | —                                                                                                                                                                                                                            |
| Developer documentation              | `has_contribution_guidelines`            | RSFC                         | `human_code_review_requirement`, `code_documentation_coverage_ok`                                                                                                                                                            |
| Testing                              | `software_has_tests`                     | RSFC                         | `passed_tests_ok`, `software_test_coverage`, `has_ci-tests`, `functional_correctness`, `repository_workflows`                                                                                                                |
| Software Engineering quality         | `uses_tool_for_warnings_and_mistakes`    | **none**                     | `has_no_linting_issues`, `code_smells_ok`, `cyclomatic_complexity_ok`, `code_duplication_ok`, `maintainability_index_ok`, `internal_cohesion_ok`, `coupling_between_objects_ok`, `lines_of_code_ok`, `dependency_management` |
| Packaging                            | `has_published_package`                  | OEBFAIR, OpenSSF Scorecard   | `software_is_containerized`, `has_releases`                                                                                                                                                                                  |
| Maintenance                          | `project_is_active`                      | OpenSSF Scorecard            | `has_active_contributors`, `code_churn_ok`                                                                                                                                                                                   |
| Support                              | `support_issue_tracking`                 | **none**                     | `has_active_communication_channels`, `response_timeframe_ok`                                                                                                                                                                 |
| Risk analysis                        | `static_analysis_common_vulnerabilities` | OpenSSF Scorecard            | `no_critical_vulnerability`, `no_leaked_credentials`, `has_no_binary_artifacts`, `uses_fuzzing`                                                                                                                              |

All 47 catalog indicators are accounted for: 14 as unambiguous validators (one per requirement) + 33 distinct indicators as participating evidence (`dependency_management` counted once despite the double listing).


## Open items

- **Table numbering inconsistency in the sources.** v1 cites "table 6.1.4," v2 cites "Table 4." I could not fetch the PDF directly this session (network restriction on the sandbox) to confirm which numbering is correct in the published guide — worth a quick manual check before this goes external.
- **Tools-that-measure-indicator column dropped.** v1 listed tools (RSFC, SOMEF, howfairis, etc.) per indicator. I did not verify those against current tool capabilities this session, so I left the column out rather than propagate unverified claims. If you want it back, that's a separate verification pass — tool coverage changes faster than indicator definitions.
- **Unambiguous/participating calls are judgment, not derived from the catalog.** The EVERSE metadata doesn't label indicators as "sufficient" vs. "supporting" — that split is my read of each indicator's description against the guide's practice text. Worth a second pair of eyes on the borderline ones: `archived_in_scholarly_repository` (Repository) and `has_no_linting_issues` (SE quality) are the two I'd flag as closest calls, since both could arguably swap into the unambiguous column.