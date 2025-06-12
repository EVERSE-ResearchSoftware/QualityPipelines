#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Optional
import json


@dataclass(frozen=True)
class Context:
    """A basic context to hold"""

    github_token: Optional[str] = None


class Configuration:
    """
    A basic wrapper for the configuration.
    """

    def __init__(self, filepath):
        with open(filepath) as f:
            self._cfg = json.load(f)


class Summary:
    """
    Summary of the results of the checks.
    """

    def __init__(self):
        self.checks = []

    def add_indicator_result(self, indicator, checking_software, status):
        self.checks.append(
            {
                "checking_software": {
                    "name": checking_software.name,
                    "id": checking_software.id,
                    "version": checking_software.version,
                },
                "indicator": indicator,
                "status": status,
            }
        )

    def to_json(self, filename):
        with open(filename, "w") as f:
            json.dump(self.checks, f, indent=4)
