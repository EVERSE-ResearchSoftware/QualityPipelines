#!/usr/bin/env python3
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
import json

from resqui.api import APIClient


@dataclass(frozen=True)
class Context:
    """A basic context to hold"""

    github_token: Optional[str] = None
    dashverse_token: Optional[str] = None


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
    raw_value: Optional[str] = None
    threshold: Optional[str] = None

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
        software = {
            "@type": "schema:SoftwareApplication",
            "name": checking_software.name,
            "softwareVersion": checking_software.version,
        }
        if checking_software.id:
            software["@id"] = checking_software.id

        check = {
            "@type": "CheckResult",
            "assessesIndicator": {"@id": indicator["@id"]},
            "checkingSoftware": software,
            "process": result.process,
            "status": {"@id": result.status_id},
            "output": result.output,
            "evidence": result.evidence,
        }
        if result.raw_value is not None:
            check["raw_value"] = result.raw_value
        if result.threshold is not None:
            check["threshold"] = result.threshold
        self.checks.append(check)

    def to_json(self):
        return json.dumps(
            {
                "@context": "https://w3id.org/everse/rsqa/0.0.3",
                "@type": "SoftwareQualityAssessment",
                "name": f"Quality assessment for {self.project_name}",
                "description": (
                    f"Automated quality assessment of {self.project_name} "
                    f"({self.branch_hash_or_tag}) run by resqui."
                ),
                "dateCreated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "license": {"@id": "https://creativecommons.org/publicdomain/zero/1.0/"},
                "creator": {"@type": "schema:Person", "name": "Quality Pipeline"},
                "assessedSoftware": {
                    "@type": "schema:SoftwareApplication",
                    "name": self.project_name,
                    "softwareVersion": self.software_version,
                    "url": self.repo_url,
                },
                "checks": self.checks,
            },
            sort_keys=True,
            indent=4,
        )

    def write(self, filename):
        with open(filename, "w") as f:
            f.write(self.to_json())

    def upload(self, dashverse_token=None):
        api = APIClient(dashverse_token)
        api.post(self.to_json())
