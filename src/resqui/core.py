#!/usr/bin/env python3
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import json

from resqui.api import APIClient


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

    def __init__(
        self,
        author,
        email,
        project_name,
        repo_url,
        software_version,
        branch_hash_or_tag,
    ):
        self.author = author
        self.email = email
        self.project_name = project_name
        self.repo_url = repo_url
        self.software_version = software_version
        self.branch_hash_or_tag = branch_hash_or_tag
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

    def to_json(self):
        return json.dumps(
            {
                #                "@context": "https://w3id.org/everse/rsqa/0.0.1/",
                #                "@type": "SoftwareQualityAssessment",
                "name": "resqui Test Assessment",
                "description": "",
                "creator": [
                    {
                        "@type": "schema:Person",
                        "name": self.author,
                        "email": self.email,
                    }
                ],
                "dateCreated": str(datetime.now()),
                "license": {
                    "@id": "https://creativecommons.org/publicdomain/zero/1.0/"
                },
                "assessedSoftware": {
                    "@type": "schema:SoftwareApplication",
                    "name": self.project_name,
                    "softwareVersion": self.software_version,
                    "url": self.repo_url,
                    "schema:identifier": {
                        "@id": "https://doi.org/10.5281/zenodo.8224012"
                    },
                },
                "checks": self.checks,
            }
        )

    def write(self, filename):
        with open(filename, "w") as f:
            json.dump(
                self.to_json(),
                f,
                indent=4,
            )

    def upload(self):
        api = APIClient()
        api.post(self.to_json())
