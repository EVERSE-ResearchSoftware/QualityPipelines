#!/usr/bin/env python3
from datetime import datetime
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


@dataclass
class CheckResult:
    """
    Datatype for indicator check results.
    """

    process: str = "Undefined process"
    status_id: str = "missing"
    output: str = "missing"
    evidence: str = "missing"
    success: bool = False

    def __bool__(self):
        return self.success


class Summary:
    """
    Summary of the software quality assessment.
    """

    def __init__(self):
        self.checks = []

    def add_indicator_result(self, indicator, checking_software, result):
        self.checks.append(
            {
                "@type": "CheckResult",
                "assessesIndicator": {"@id": indicator["@id"]},
                "checkingSoftware": {
                    "@type": "schema:SoftwareApplication",
                    "name": checking_software.name,
                    "@id": checking_software.id,
                    "softwareVersion": checking_software.version,
                },
                "process": result.process,
                "status": {"@id": result.status_id},
                "output": result.output,
                "evidence": result.evidence,
            }
        )

    def to_json(self, filename):
        with open(filename, "w") as f:
            json.dump(
                {
                    "@context": "https://w3id.org/everse/rsqa/0.0.1/",
                    "@type": "SoftwareQualityAssessment",
                    "dateCreated": str(datetime.now()),
                    "license": {
                        "@id": "https://creativecommons.org/publicdomain/zero/1.0/"  # noqa: E501
                    },
                    "checks": self.checks,
                },
                f,
                indent=4,
            )
