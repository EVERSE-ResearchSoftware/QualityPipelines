import json
import os

from resqui.plugins.base import IndicatorPlugin
from resqui.executors import DockerExecutor
from resqui.core import CheckResult
from resqui.workspace import create_workspace


class RSFC(IndicatorPlugin):
    name = "RSFC"
    id = "https://w3id.org/everse/tools/rsfc"
    version = "0.1.7"
    image_url = f"docker.io/amonterodx/rsfc:{version}"
    indicators = [
        "persistent_and_unique_identifier",
        "requirements_specified",
        "has_releases",
        "software_has_citation",
        "software_has_license",
        "software_has_documentation",
        "descriptive_metadata",
        "versioning_standards_use",
        "version_control_use",
        "software_has_tests",
        "repository_workflows",
        "archived_in_software_heritage",
        "has_contribution_guidelines",
        "software_is_containerized"
    ]

    def __init__(self, context):
        self.context = context
        self.executor = DockerExecutor(self.image_url)
        self._cache = {}

    def execute(self, url, commit_hash):
        cache_key = (url, commit_hash)
        if cache_key in self._cache:
            return self._cache[cache_key]

        url = url.removesuffix(".git")

        assessment_filename = "rsfc_assessment.json"


        with create_workspace(prefix="resqui-rsfc-") as workspace:
            if workspace.is_shared:
                container_workspace = workspace.container_path("/rsfc")
                run_args = [
                    "--rm",
                    *workspace.docker_mount_args("/rsfc"),
                    "-w",
                    container_workspace,
                ]
                assessment_fpath = os.path.join(
                    workspace.local_path, "rsfc_output", assessment_filename
                )
            else:
                run_args = [
                    "--rm",
                    *workspace.docker_mount_args("/rsfc/rsfc_output"),
                ]
                assessment_fpath = os.path.join(workspace.local_path, assessment_filename)

            command = ["--repo", url]
            if self.context.github_token:
                command += ["-t", self.context.github_token]

            _ = self.executor.run(command, run_args=run_args)

            if not os.path.isfile(assessment_fpath):
                msg = f"Error: RSFC did not generate the expected assessment file named '{assessment_filename}'"
                raise FileNotFoundError(msg)

            with open(assessment_fpath) as f:
                report = json.load(f)
                
        # New remapping for better management
        checks_by_id = {}
        
        for check in report.get("checks", []):
            test_id_completo = check.get("test_id", "")
            test_id_corto = test_id_completo.split("/")[-1]
            
            if test_id_corto:
                checks_by_id[test_id_corto] = check
                
        report = checks_by_id

        self._cache[cache_key] = report

        return report

    def persistent_and_unique_identifier(self, url, branch_hash_or_tag):
        
        # Last version (do not erase)
        '''report = self.execute(url, branch_hash_or_tag)
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

        return check_list'''
        
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-01-1"]
        if check["output"] == "true":
            success = True
        else:
            success = False
        check = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )
        
        return check


    def software_has_documentation(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-05-3"]
        if check["output"] == "true":
            success = True
        else:
            success = False
        check = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )
        
        return check

    def requirements_specified(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-13-1"]
        if check["output"] == "true":
            success = True
        else:
            success = False
        check = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )
        
        return check

    def has_releases(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-03-1"]
        if check["output"] == "true":
            success = True
        else:
            success = False
        check = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )
        
        return check

    def software_has_license(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-15-1"]
        if check["output"] == "true":
            success = True
        else:
            success = False
        check = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )
        
        return check

    def descriptive_metadata(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-04-4"]
        if check["output"] == "true":
            success = True
        else:
            success = False
        check = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )
        
        return check

    def versioning_standards_use(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-03-6"]
        if check["output"] == "true":
            success = True
        else:
            success = False
        check = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )
        
        return check

    def version_control_use(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-09-1"]
        if check["output"] == "true":
            success = True
        else:
            success = False
        check = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )
        
        return check

    def software_has_tests(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-14-1"]
        if check["output"] == "true":
            success = True
        else:
            success = False
        check = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )
        
        return check

    def software_has_citation(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-18-1"]
        if check["output"] == "true":
            success = True
        else:
            success = False
        check = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )
        
        return check

    def repository_workflows(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-19-1"]
        if check["output"] == "true":
            success = True
        else:
            success = False
        check = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )
        
        return check

    def archived_in_software_heritage(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-08-1"]
        if check["output"] == "true":
            success = True
        else:
            success = False
        check = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )
        
        return check
    
    def has_contribution_guidelines(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-21-1"]
        if check["output"] == "true":
            success = True
        else:
            success = False
        check = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )
        
        return check

    def software_is_containerized(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-22-1"]
        if check["output"] == "true":
            success = True
        else:
            success = False
        check = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success,
                )
        
        return check