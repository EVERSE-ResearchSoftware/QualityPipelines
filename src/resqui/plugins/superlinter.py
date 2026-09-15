import os
import platform
import re
import shutil
import subprocess

from resqui.plugins import IndicatorPlugin
from resqui.executors import DockerExecutor
from resqui.core import CheckResult
from resqui.workspace import create_workspace


class SuperLinter(IndicatorPlugin):
    name = "SuperLinter"
    version = "8.7.0"
    image_url = f"ghcr.io/super-linter/super-linter:v{version}"
    id = "https://w3id.org/everse/tools/superlinter"
    indicators = ["has_no_linting_issues"]

    def __init__(self, context):
        self.context = context
        machine = platform.machine()
        pull_args = ["--platform", "linux/amd64"] if machine == "arm64" else []
        self.executor = DockerExecutor(self.image_url, pull_args=pull_args)

    def has_no_linting_issues(self, url, branch):

        with create_workspace(prefix="resqui-superlinter-") as workspace:
            try:
                subprocess.run(
                    ["git", "clone", url, workspace.local_path],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except subprocess.CalledProcessError as e:
                print(f"Error cloning {url}: {e}")
                raise

            lint_path = workspace.container_path("/tmp/lint")

            run_args = [
                "--rm",
                "-e",
                "RUN_LOCAL=true",
                "-e",
                f"DEFAULT_BRANCH={branch}",
                "-e",
                f"DEFAULT_WORKSPACE={lint_path}",
                "-e",
                "SAVE_SUPER_LINTER_SUMMARY=true",
                "--user",
                f"{os.getuid()}:{os.getgid()}",
                *workspace.docker_mount_args("/tmp/lint"),
            ]

            p = self.executor.run([], run_args=run_args)

            summary_path = os.path.join(
                workspace.local_path,
                "super-linter-output",
                "super-linter-summary.md",
            )

            if "Super-linter detected linting errors" in p.stdout:
                failed_linters = self.get_failed_linters(summary_path)

                summary_destination = os.path.abspath(
                    os.path.join(
                        os.getcwd(),
                        "super-linter-summary.md",
                    )
                )

                shutil.copy2(summary_path, summary_destination)

                output = "false"

                if failed_linters:
                    evidence = (
                        "Super-linter detected linting errors with the "
                        f"following linters: {', '.join(failed_linters)}. "
                        f"You can check the detailed errors in "
                        f"{summary_destination}"
                    )
                else:
                    evidence = (
                        "Super-linter detected linting errors. "
                        f"You can check the detailed errors in "
                        f"{summary_destination}"
                    )

                success = False

            else:
                output = "true"
                evidence = "No linting errors have been detected."
                success = True

        return CheckResult(
            process="Searches for linting errors.",
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )

    def get_failed_linters(self, summary_path):
        """
        Return the names of the linters that reported failures.
        """

        with open(summary_path, "r", encoding="utf-8") as f:
            content = f.read()

        failed_linters = re.findall(
            r"^\|\s*([A-Z0-9_]+)\s*\|\s*Fail\s*❌\s*\|",
            content,
            re.MULTILINE,
        )

        return failed_linters