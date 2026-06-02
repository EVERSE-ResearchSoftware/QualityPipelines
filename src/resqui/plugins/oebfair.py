import json
import tempfile
import os
import shutil

from resqui.plugins.base import IndicatorPlugin
from resqui.executors import DockerExecutor
from resqui.core import CheckResult


class OEBFAIR(IndicatorPlugin):
    name = "OEBFAIR"
    id = "https://w3id.org/everse/tools/fairsoft-evaluator"
    version = "0.2.2"
    image_url = f"registry.gitlab.bsc.es/everse/resqui-oeb-plugin/resqui-oebfair:v0.2.2"
    indicators = [
        "unique_identifier",
        "has_package",
        "has_citation",
        "has_license",
        "has_documentation",
        "descriptive_metadata",
        "listed_in_registry"
    ]

    def __init__(self, context):
        self.context = context
        self.executor = DockerExecutor(self.image_url)
        self._cache = {}

    def execute(self, url, commit_hash):
        cache_key = (url, commit_hash)
        if cache_key in self._cache:
            return self._cache[cache_key]

        tempdir = tempfile.mkdtemp()

        url = url.removesuffix(".git")

        run_args = [
            "--rm",
            "-v",
            f"{tempdir}:/oebfair/oebfair_output"
        ]

        _ = self.executor.run(["--repo", url, "-t", f"{self.context.github_token}"], run_args=run_args)

        assessment_filename = "oebfair_assessment.json"
        assessment_fpath = os.path.join(tempdir, assessment_filename)
        if not os.path.isfile(assessment_fpath):
            msg = f"Error: OEBFAIR did not generate the expected assessment file named '{assessment_fpath}'"
            raise FileNotFoundError(msg)

        with open(assessment_fpath) as f:
            report = json.load(f)

        shutil.rmtree(tempdir)

        self._cache[cache_key] = report

        return report

    def unique_identifier(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []

        for check in checks:
            if "persistent_and_unique_identifier" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False

                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )

                check_list.append(check_res)

        return check_list

    def has_package(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []

        for check in checks:
            if "has_published_package" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False

                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success
                )

                check_list.append(check_res)

        return check_list

    def has_documentation(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []

        for check in checks:
            if "software_has_documentation" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False

                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )

                check_list.append(check_res)

        return check_list

    def has_releases(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []

        for check in checks:
            if "has_releases" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False

                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )

                check_list.append(check_res)

        return check_list

    def has_license(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)

        checks = report["checks"]
        check_list = []

        for check in checks:
            if "software_has_license" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False

                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )

                check_list.append(check_res)

        return check_list

    def descriptive_metadata(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []

        for check in checks:
            if "descriptive_metadata" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False

                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )

                check_list.append(check_res)

        return check_list

    def listed_in_registry(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []

        for check in checks:
            if "listed_in_registry" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False

                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )

                check_list.append(check_res)

        return check_list

    def versioning_standards_use(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []

        for check in checks:
            if "versioning_standards_use" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False

                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )

                check_list.append(check_res)

        return check_list

    def version_control_use(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []

        for check in checks:
            if "version_control_use" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False

                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )

                check_list.append(check_res)

        return check_list

    def software_has_tests(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []

        for check in checks:
            if "software_tests" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False

                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )

                check_list.append(check_res)

        return check_list

    def has_citation(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []

        for check in checks:
            if "software_has_citation" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False

                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )

                check_list.append(check_res)

        return check_list

    def repository_workflows(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []

        for check in checks:
            if "repository_workflows" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False

                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )

                check_list.append(check_res)

        return check_list

    def archived_in_software_heritage(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []

        for check in checks:
            if "archived_in_software_heritage" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False

                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )

                check_list.append(check_res)

        return check_list
