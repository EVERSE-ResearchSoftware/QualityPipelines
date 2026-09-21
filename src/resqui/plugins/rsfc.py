import json
import os
import shutil

from resqui.plugins.base import IndicatorPlugin
from resqui.executors import DockerExecutor
from resqui.core import CheckResult
from resqui.workspace import create_workspace


class RSFC(IndicatorPlugin):
    name = "RSFC"
    id = "https://w3id.org/everse/tools/rsfc"
    version = "0.2.0"
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
        "has_active_contributors",
        "support_issue_tracking",
        "codemeta_completeness",
        "software_has_tests",
        "repository_workflows",
        "archived_in_software_heritage",
        "has_contribution_guidelines",
        "software_is_containerized",
        "archived_in_scholarly_repository",
        "has_active_communication_channels"
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
        cached_somef_output_fpath = self.somef_output_path(url, commit_hash)

        with create_workspace(prefix="resqui-rsfc-") as workspace:
            if workspace.is_shared:
                container_workspace = workspace.container_path("/rsfc")
                rsfc_output_dir = os.path.join(workspace.local_path, "rsfc_output")
                generated_somef_fpath = os.path.join(rsfc_output_dir, "somef_assessment.json")

                metadata_local_fpath = os.path.join(workspace.local_path, "somef_output.json")
                metadata_container_fpath = os.path.join(container_workspace, "somef_output.json")
                
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
                generated_somef_fpath = os.path.join(workspace.local_path, "somef_assessment.json")

                metadata_local_fpath = os.path.join(workspace.local_path, "somef_output.json")
                metadata_container_fpath = "/rsfc/rsfc_output/somef_output.json"
                run_args = [
                    "--rm",
                    *workspace.docker_mount_args("/rsfc/rsfc_output"),
                ]
                assessment_fpath = os.path.join(workspace.local_path, assessment_filename)

            command = ["--repo", url]
            if os.path.isfile(cached_somef_output_fpath):
                shutil.copyfile(cached_somef_output_fpath, metadata_local_fpath)
                command += ["--metadata", metadata_container_fpath]
            else:
                command += ["-s"]
                
            if self.context.github_token:
                command += ["-t", self.context.github_token]
            _ = self.executor.run(command, run_args=run_args)

            if not os.path.isfile(assessment_fpath):
                msg = f"Error: RSFC did not generate the expected assessment file named '{assessment_filename}'"
                raise FileNotFoundError(msg)

            with open(assessment_fpath) as f:
                report = json.load(f)
            
            if (    
            not os.path.isfile(cached_somef_output_fpath)
            and os.path.isfile(generated_somef_fpath)
        ):
                os.makedirs(os.path.dirname(cached_somef_output_fpath), exist_ok=True)
                shutil.copyfile(generated_somef_fpath, cached_somef_output_fpath)        
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

    def software_id(self, url):
        return (
            url.removesuffix(".git")
            .replace("https://github.com/", "")
            .replace("http://github.com/", "")
            .rstrip("/")
            .replace("/", "_")
        )

    def ref_id(self, ref):
        return str(ref).replace("/", "_").replace(":", "_")

    def somef_output_path(self, url, commit_hash):
        return os.path.join(
            "tmp",
            "somef_outputs",
            self.software_id(url),
            self.ref_id(commit_hash),
            "somef_output.json",
        )

    def archived_in_scholarly_repository(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-08-2"]
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
    
    def has_active_communication_channels(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-05-4"]
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
    
    def support_issue_tracking(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-20-1"]
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
    
    def has_active_contributors(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        check = report["RSFC-06-2"]
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

    def codemeta_completeness(self, url, branch_hash_or_tag):
        codemeta_process = (
            "RSFC-01-2",
            "RSFC-03-6",
            "RSFC-04-1",
            "RSFC-04-3",
            "RSFC-04-4",
            "RSFC-06-1",
            "RSFC-06-2",
            "RSFC-16-1",
            "RSFC-20-1",
        )
        report = self.execute(url, branch_hash_or_tag)
        checks = [
            (check_id, report[check_id])
            for check_id in codemeta_process
            if check_id in report
        ]
        codemeta_checks = [
            (check_id, check)
            for check_id, check in checks
            if "codemeta" in check["evidence"].lower()
        ]
        outputs = []
        output = "false"
        for _, check in codemeta_checks:
            outputs.append(check["output"])

        true_count = outputs.count("true")
        total_count = len(outputs)
        percentage = (
            (true_count / total_count) * 100
            if total_count > 0
            else 0
        )
        if percentage >= 70:
            success = True
            output = "true"
        else:
            success = False
            output = "false"

        passed_check_ids = [
            check_id
            for check_id, check in codemeta_checks
            if check["output"] == "true"
        ]
        passed_checks_text = ", ".join(passed_check_ids) or "none"
        
        process_lines = [
            f"- {check_id}: {check['output']}"
            for check_id, check in codemeta_checks
        ]

        process_output = "\n".join(process_lines)
        if not process_output:
            process_output = "- No RSFC processes with CodeMeta evidence were found."

        passed_check_ids = [
            check_id
            for check_id, check in codemeta_checks
        ]
        checks_text = ", ".join(passed_check_ids) or "none"
        
        evidence = (
            f"CodeMeta completeness achieved: {percentage:.2f}% "
            f"({true_count}/{total_count} processes passed).\n\n"
            "CodeMeta test outputs:\n"
            + process_output
        )
        check = CheckResult(
            process=(
                f"This check runs the tests {checks_text} in search of codemeta "
                "mention in their results. Test descriptions are available in "
                "https://oeg-upm.github.io/rsfc/doc/catalog.html#test"
            ),
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )

        return check

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
