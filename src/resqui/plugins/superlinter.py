import platform
import subprocess
import tempfile
import shutil
import os

from resqui.plugins import IndicatorPlugin
from resqui.executors import DockerExecutor
from resqui.core import CheckResult


class SuperLinter(IndicatorPlugin):
    name = "SuperLinter"
    version = "7.3.0"
    image_url = f"ghcr.io/super-linter/super-linter:v{version}"
    id = "https://w3id.org/everse/tools/superlinter"
    indicators = ["has_no_linting_issues"]

    def __init__(self, context):
        self.context = context
        machine = platform.machine()
        pull_args = ["--platform", "linux/amd64"] if machine == "arm64" else []
        self.executor = DockerExecutor(self.image_url, pull_args=pull_args)

    def has_no_linting_issues(self, url, branch):
        temp_dir = tempfile.mkdtemp()

        try:
            subprocess.run(
                ["git", "clone", url, temp_dir],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error cloning {url}: {e}")
            raise

        run_args = [
            #            "-e",
            #            "LOG_LEVEL=DEBUG",
            "-e",
            "RUN_LOCAL=true",
            "-e",
            f"DEFAULT_BRANCH={branch}",
            "-v",
            f"{temp_dir}:/tmp/lint",
        ]
        p = self.executor.run([], run_args=run_args)

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        if "Super-linter detected linting errors" in p.stdout:
            output = "invalid"
            evidence = "Linting errors have been detected."
            success = False
        else:
            output = "valid"
            evidence = "No linting errors have been detected."
            success = True

        # print("STDOUT")
        # print(p.stdout)
        # print()
        # print("STDERR")
        # print(p.stderr)

        return CheckResult(
            process="Searches for linting errors.",
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )
