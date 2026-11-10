import json
import tempfile
import os
import shutil
import subprocess

from resqui.plugins.base import IndicatorPlugin
from resqui.executors import DockerExecutor
from resqui.core import CheckResult
from resqui.workspace import create_workspace

SOFTWARE_APPLICATION_ID = "https://w3id.org/everse/tools/semgrep"
SOFTWARE_APPLICATION_VERSION = "1.183.0"
SOFTWARE_APPLICATION_NAME = "Semgrep"

class Semgrep(IndicatorPlugin):
    """Evaluates security vulnerabilities with the semgrep
    [Semgrep Tool](https://semgrep.dev/).

    Languages: language-independent.
    """

    name = SOFTWARE_APPLICATION_NAME
    id = SOFTWARE_APPLICATION_ID
    version = SOFTWARE_APPLICATION_VERSION

    image_url = f"semgrep/semgrep:1.183.0"
    indicators = [
        "no_critical_vulnerability"
    ]
    requires = ["docker"]

    def __init__(self, context):
        self.context = context
        self.executor = DockerExecutor(self.image_url)
        self._cache = {}

    def no_critical_vulnerability(self, url, commit_hash):

        check_res = CheckResult(
            process="Check software for critical vulnerabilities.",
            status_id="schema:CompletedActionStatus",
        )

        report_fname = "report.json"

        with create_workspace(prefix="resqui-semgrep-") as workspace:
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

            plugin_path = workspace.container_path("/semgrep")
            report_path = f"{plugin_path}/{report_fname}"


            run_args = ["--rm", *workspace.docker_mount_args("/semgrep")]

            p = self.executor.run(["semgrep", "scan", "--json", f"--json-output={report_path}", plugin_path], run_args=run_args)

            with open(os.path.join(workspace.local_path, report_fname)) as f:
                report = json.load(f)

            evidence = ""
            results = report.get('results', [])
            for result in results:
                extra = result.get('extra')
                if extra and extra.get('severity') == 'CRITICAL':
                    evidence = evidence + extra.get('message', '') + "\n"

            check_res.success = not evidence
            check_res.output = str(not evidence).lower()
            check_res.evidence = evidence

        return check_res
