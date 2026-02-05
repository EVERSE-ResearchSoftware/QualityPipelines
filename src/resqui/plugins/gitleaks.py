import json
import subprocess
import tempfile
import shutil
import os

from resqui.plugins.base import IndicatorPlugin
from resqui.executors import DockerExecutor
from resqui.core import CheckResult


class Gitleaks(IndicatorPlugin):
    name = "GitLeaks"
    version = "8.24.2"
    image_url = f"ghcr.io/gitleaks/gitleaks:v{version}"
    id = "https://w3id.org/everse/tools/gitleaks"
    indicators = ["has_no_security_leak"]

    def __init__(self, context):
        self.context = context
        self.executor = DockerExecutor(self.image_url)

    def has_no_security_leak(self, url, branch_hash_or_tag):
        temp_dir = tempfile.mkdtemp()
        report_fname = "report.json"

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

        run_args = ["-v", f"{temp_dir}:/path"]
        p = self.executor.run(
            ["git", "/path", "-r", f"/path/{report_fname}"], run_args=run_args
        )
        with open(os.path.join(temp_dir, report_fname)) as f:
            report = json.load(f)

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        if "no leaks found" in p.stderr and not report:
            output = "secure"
            evidence = "No leaks have been found."
            success = True
        else:
            output = "insecure"
            evidence = "Leaks have been found."
            success = False

        return CheckResult(
            process="Searches for security leaks in the full repository history.",
            status_id="Pass" if success else "Fail",
            output=output,
            evidence=evidence,
            success=success,
        )
