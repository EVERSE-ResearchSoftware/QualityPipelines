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
