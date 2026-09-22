import json
import os
import shutil

from resqui.core import CheckResult
from resqui.executors import DockerExecutor
from resqui.plugins.base import IndicatorPlugin
from resqui.workspace import create_workspace


class Rsmetacheck(IndicatorPlugin):
    name = "rsmetacheck"
    id = "https://github.com/SoftwareUnderstanding/rsmetacheck"
    version = "0.3.6"
    image_url = f"docker.io/sergiozsz/rsmetacheck:{version}"
    indicators = ["metadata_is_up_to_date"]

    def __init__(self, context):
        self.context = context
        self.executor = DockerExecutor(self.image_url)
        self._cache = {}

    def execute(self, url, commit_hash):
        cache_key = (url, commit_hash)
        if cache_key in self._cache:
            return self._cache[cache_key]

        url = url.removesuffix(".git")

        analysis_filename = "analysis_results.json"
        somef_output_dir = "somef_outputs"
        pitfalls_output_dir = "pitfalls_outputs"
        cached_somef_output_fpath = self.somef_output_path(url, commit_hash)

        with create_workspace(prefix="resqui-rsmetacheck-") as workspace:
            container_workspace = workspace.container_path("/workspace")
            run_args = [
                "--rm",
                *workspace.docker_mount_args("/workspace"),
                "-w",
                container_workspace,
                "-e",
                "SOMEF_DOWNLOAD_LIMIT_MB=1000",
            ]

            if self.context.github_token:
                run_args += ["-e", f"SOMEF_GITHUB_TOKEN={self.context.github_token}"]

            analysis_container_path = os.path.join(
                container_workspace, analysis_filename
            )
            analysis_fpath = os.path.join(workspace.local_path, analysis_filename)

            pitfalls_container_path = os.path.join(
                container_workspace, pitfalls_output_dir
            )

            if os.path.isfile(cached_somef_output_fpath):
                somef_input_fpath = os.path.join(
                    workspace.local_path, "somef_output.json"
                )
                shutil.copyfile(cached_somef_output_fpath, somef_input_fpath)
                command = [
                    "rsmetacheck",
                    "--skip-somef",
                    "--input",
                    os.path.join(container_workspace, "somef_output.json"),
                    "--pitfalls-output",
                    pitfalls_container_path,
                    "--analysis-output",
                    analysis_container_path,
                ]
            else:
                command = [
                    "rsmetacheck",
                    "--input",
                    url,
                    "--somef-output",
                    os.path.join(container_workspace, somef_output_dir),
                    "--pitfalls-output",
                    pitfalls_container_path,
                    "--analysis-output",
                    analysis_container_path,
                ]

            result = self.executor.run(command, run_args=run_args)
            if not os.path.isfile(analysis_fpath):
                if result.returncode != 0:
                    raise ValueError(
                        "rsmetacheck Docker execution failed:\n"
                        f"stdout:\n{result.stdout}\n"
                        f"stderr:\n{result.stderr}"
                    )
                msg = (
                    "Error: rsmetacheck did not generate the expected analysis "
                    f"file named '{analysis_filename}'"
                )
                raise FileNotFoundError(msg)

            with open(analysis_fpath, encoding="utf-8") as f:
                report = json.load(f)

            generated_somef_output_fpath = os.path.join(
                workspace.local_path, somef_output_dir, "output_1.json"
            )
            if (
                not os.path.isfile(cached_somef_output_fpath)
                and os.path.isfile(generated_somef_output_fpath)
            ):
                os.makedirs(os.path.dirname(cached_somef_output_fpath), exist_ok=True)
                shutil.copyfile(generated_somef_output_fpath, cached_somef_output_fpath)

        self._cache[cache_key] = report

        return report


    def metadata_is_up_to_date(self, url, branch_hash_or_tag):
        useful_checks = ("P001",
                                "P012",
                                "P016",
                                "P017",
                                "W002")
        
        report = self.execute(url, branch_hash_or_tag)
        checks = report.get("pitfalls & warnings")  
        
        
        if checks is None:
            return CheckResult(
                process=(
                        f"this check run the tests {useful_checks} from RsMetaCheck. "
                        f"More information about the tests can be found at "
                        f"https://github.com/SoftwareUnderstanding/rsmetacheck/blob/main/docs/catalog.md"
                        
                        ),
                status_id="schema:FailedActionStatus",
                output="error",
                evidence=(
                    "RSMetaCheck analysis output does not contain the expected "
                    "'pitfalls & warnings' section."
                ),
                success=False,
            )
        
        failed_checks = []
        passed_checks = []
        for check in checks:
            
            code = check.get("pitfall_code") or check.get("warning_code")
            count = check.get("count", 0)
            if code in useful_checks:
                if count > 0:
                    failed_checks.append(check)
                else:
                    passed_checks.append(check)
        
        success = len(failed_checks) == 0
        output = "true" if success else "false"
        if not success:
            evidence = "The following RSMetaCheck findings were detected:\n"
            for check in failed_checks:
                code = check.get("pitfall_code") or check.get("warning_code")
                description = check.get("warning_desc", "") or check.get("pitfall_desc", "")
                count = check.get("count", 0)
                evidence += f"- {code}: {description} (count: {count})\n"
        else:
            evidence = "The following RSMetaCheck findings were not detected:\n"
            for check in passed_checks:
                code = check.get("pitfall_code") or check.get("warning_code")
                description = check.get("warning_desc", "") or check.get("pitfall_desc", "")
                evidence += f"- {code}: {description} (count: 0)\n"
                
        status_id = "schema:CompletedActionStatus"
        return CheckResult(
            process=(
            f"this check run the tests {useful_checks} from RsMetaCheck. "
            f"More information about the tests can be found at "
            f"https://github.com/SoftwareUnderstanding/rsmetacheck/blob/main/docs/catalog.md"
    
            ),
            success=success,
            output=output,
            evidence=evidence,
            status_id=status_id,
        )

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
