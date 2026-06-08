import json
import subprocess
import os

from resqui.plugins.base import IndicatorPlugin
from resqui.executors import DockerExecutor
from resqui.core import CheckResult
from resqui.workspace import create_workspace


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
        report_fname = "report.json"

        # Implementacion anterior sustituida para SQOO:
        # temp_dir = tempfile.mkdtemp()
        # run_args = ["-v", f"{temp_dir}:/path"]
        # p = self.executor.run(
        #     ["git", "/path", "-r", f"/path/{report_fname}"], run_args=run_args
        # )

        # Implementacion para SQOO: el workspace puede vivir en un volumen Docker
        # compartido para que el worker y el contenedor del plugin vean la misma ruta.
        with create_workspace(prefix="resqui-gitleaks-") as workspace:
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

            plugin_path = workspace.container_path("/path")
            report_path = f"{plugin_path}/{report_fname}"
            run_args = workspace.docker_mount_args("/path")
            p = self.executor.run(
                ["git", plugin_path, "-r", report_path], run_args=run_args
            )
            with open(os.path.join(workspace.local_path, report_fname)) as f:
                report = json.load(f)

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
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )
