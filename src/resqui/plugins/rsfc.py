import json
import os

from resqui.core import CheckResult
from resqui.executors import DockerExecutor
from resqui.plugins.base import IndicatorPlugin
from resqui.workspace import create_workspace


class RSFC(IndicatorPlugin):
    name = "RSFC"
    id = "https://w3id.org/everse/tools/rsfc"
    version = "0.1.8"
    # The RSFC Docker CLI accepts local project directory analysis with --local,
    # but the path must be inside a container-mounted volume.
    supports_local_path = True
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
        "software_is_containerized",
    ]
    local_mode_unsupported_checks = {
        "RSFC-01-1",
        "RSFC-03-1",
        "RSFC-03-2",
        "RSFC-03-3",
        "RSFC-03-4",
        "RSFC-03-5",
        "RSFC-04-1",
        "RSFC-04-5",
        "RSFC-07-2",
        "RSFC-09-1",
        "RSFC-14-1",
        "RSFC-20-1",
    }

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
                assessment_fpath = os.path.join(workspace.local_path, "rsfc_output", assessment_filename)
            else:
                run_args = [
                    "--rm",
                    *workspace.docker_mount_args("/rsfc/rsfc_output"),
                ]
                assessment_fpath = os.path.join(workspace.local_path, assessment_filename)

            if self.context.local_path is not None:
                local_project_path = os.path.abspath(self.context.local_path)
                project_container_path = "/rsfc_project"
                # add the project path as a volume to mount
                run_args += ["-v", f"{local_project_path}:{project_container_path}"]
                command = ["--local", project_container_path]
            else:
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

    def _skipped_check_result(self, check_id):
        print(f"⚠️  RSFC local mode does not run {check_id}; skipping indicator")
        return CheckResult(
            process="RSFC local mode",
            status_id="schema:FailedActionStatus",
            output="missing",
            evidence=(
                f"RSFC local analysis does not generate check '{check_id}'. The indicator is skipped for local mode."
            ),
            success=False,
        )

    def _check_result(self, report, check_id):
        if self.context.local_path is not None and check_id in self.local_mode_unsupported_checks:
            return self._skipped_check_result(check_id)

        check = report.get(check_id)
        if check is None:
            raise KeyError(f"RSFC did not generate the expected check with id '{check_id}'")

        return CheckResult(
            process=check["process"],
            status_id=check["status"]["@id"],
            output=check["output"],
            evidence=check["evidence"],
            success=check["output"] == "true",
        )

    def persistent_and_unique_identifier(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        return self._check_result(report, "RSFC-01-1")

    def software_has_documentation(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        return self._check_result(report, "RSFC-05-3")

    def requirements_specified(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        return self._check_result(report, "RSFC-13-1")

    def has_releases(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        return self._check_result(report, "RSFC-03-1")

    def software_has_license(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        return self._check_result(report, "RSFC-15-1")

    def descriptive_metadata(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        return self._check_result(report, "RSFC-04-4")

    def versioning_standards_use(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        return self._check_result(report, "RSFC-03-6")

    def version_control_use(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        return self._check_result(report, "RSFC-09-1")

    def software_has_tests(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        return self._check_result(report, "RSFC-14-1")

    def software_has_citation(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        return self._check_result(report, "RSFC-18-1")

    def repository_workflows(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        return self._check_result(report, "RSFC-19-1")

    def archived_in_software_heritage(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        return self._check_result(report, "RSFC-08-1")

    def has_contribution_guidelines(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        return self._check_result(report, "RSFC-21-1")

    def software_is_containerized(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        return self._check_result(report, "RSFC-22-1")
