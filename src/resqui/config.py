import json

DEFAULT_CONFIG = {
    "indicators": [
        {
            "name": "has_license",
            "plugin": "HowFairIs",
            "@id": "https://w3id.org/everse/i/indicators/license",
        },
        {
            "name": "has_citation",
            "plugin": "CFFConvert",
            "@id": "https://w3id.org/everse/i/indicators/citation",
        },
        {
            "name": "has_ci_tests",
            "plugin": "OpenSSFScorecard",
            "@id": "https://w3id.org/everse/i/indicators/has_ci-tests",
        },
        {
            "name": "human_code_review_requirement",
            "plugin": "OpenSSFScorecard",
            "@id": "https://w3id.org/everse/i/indicators/human_code_review_requirement",
        },
        {
            "name": "has_published_package",
            "plugin": "OpenSSFScorecard",
            "@id": "https://w3id.org/everse/i/indicators/has_published_package",
        },
        {
            "name": "has_no_security_leak",
            "plugin": "Gitleaks",
            "@id": "https://w3id.org/everse/i/indicators/has_no_security_leak",
        },
    ]
}


class Configuration:
    """
    A basic wrapper for the configuration.
    """

    def __init__(self, filepath=None):
        if filepath is None:
            print("Loading default configuration.")
            self._cfg = DEFAULT_CONFIG
        else:
            print(f"Loading configuration from '{filepath}'.")
            with open(filepath) as f:
                self._cfg = json.load(f)
