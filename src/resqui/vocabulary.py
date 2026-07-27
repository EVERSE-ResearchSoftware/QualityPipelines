"""Canonical EVERSE indicator vocabulary.

Source: https://everse.software/indicators/api/indicators.json
"""

INDICATOR_BASE_URI = "https://w3id.org/everse/i/indicators/"

MISSING_ID = "missing"

INDICATOR_SLUGS = frozenset(
    {
        "passed_tests_ok",
        "code_churn_ok",
        "code_duplication_ok",
        "code_smells_ok",
        "codemeta_completeness",
        "internal_cohesion_ok",
        "coupling_between_objects_ok",
        "cyclomatic_complexity_ok",
        "functional_correctness",
        "static_analysis_common_vulnerabilities",
        "maintainability_index_ok",
        "no_critical_vulnerability",
        "no_leaked_credentials",
        "lines_of_code_ok",
        "has_active_communication_channels",
        "has_active_contributors",
        "has_no_binary_artifacts",
        "project_is_active",
        "response_timeframe_ok",
        "versioning_standards_use",
        "repository_workflows",
        "has_ci-tests",
        "dependency_management",
        "descriptive_metadata",
        "software_has_documentation",
        "software_has_license",
        "has_no_linting_issues",
        "persistent_and_unique_identifier",
        "has_releases",
        "software_test_coverage",
        "metadata_is_up_to_date",
        "archived_in_software_heritage",
        "archived_in_scholarly_repository",
        "listed_in_registry",
        "has_published_package",
        "version_control_use",
        "support_issue_tracking",
        "software_has_tests",
        "has_contribution_guidelines",
        "human_code_review_requirement",
        "requirements_specified",
        "uses_tool_for_warnings_and_mistakes",
        "software_has_license_for_file_types",
        "software_has_citation",
        "uses_fuzzing",
        "code_documentation_coverage_ok",
        "software_is_containerized",
    }
)

KNOWN_INDICATOR_IDS = frozenset(INDICATOR_BASE_URI + slug for slug in INDICATOR_SLUGS)


def is_known_indicator_id(indicator_id):
    """
    Whether `indicator_id` is either the "missing" sentinel or a W3ID URI
    listed in the EVERSE indicator vocabulary.
    """
    return indicator_id == MISSING_ID or indicator_id in KNOWN_INDICATOR_IDS
