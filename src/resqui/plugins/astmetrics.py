import json
import subprocess

from pathlib import Path
from resqui.plugins.base import IndicatorPlugin
from resqui.executors import PythonExecutor
from resqui.core import CheckResult
from resqui.workspace import create_workspace

TIMEOUT_SECONDS = 600

class ASTMetrics(IndicatorPlugin):
    name = "ASTMetrics"
    version = "0.43.1"
    id = "https://w3id.org/everse/tools/ast-metrics"  
    indicators = ["maintainability_index_ok"]

    def __init__(self, context):
        self.context = context
        self.executor = PythonExecutor()
        self.executor.install(f"ast-metrics=={self.version}")
        self._cache = {}

    def execute(self, url, branch=None):
        cache_key = (url, branch)
        if cache_key in self._cache:
            return self._cache[cache_key]

        bin_path = f"{self.executor.temp_dir}/bin/ast-metrics"
        with create_workspace(prefix="resqui-astmetrics-") as ws:
            subprocess.run(["git", "clone", "--", url, ws.local_path], check=True,
                            timeout=TIMEOUT_SECONDS,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if branch:
                subprocess.run(["git", "checkout", branch], check=True, cwd=ws.local_path,
                                timeout=TIMEOUT_SECONDS,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            report_path = Path(ws.local_path) / "ast-metrics-report.json"
            subprocess.run(
                [bin_path, "analyze", f"--report-json={report_path}", "."],
                cwd=ws.local_path, timeout=TIMEOUT_SECONDS,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            report = json.loads(report_path.read_text()) if report_path.exists() else {}

        self._cache[cache_key] = report
        return report

    def maintainability_index_ok(self, url, branch=None):
        report = self.execute(url, branch)

        if not report.get("numberFiles"):
            return CheckResult(
                process="Measures maintainability index using ast-metrics.",
                status_id="schema:CompletedActionStatus",
                output="indeterminate",
                evidence="No files were analyzed by ast-metrics.",
                success=True,
            )
        # averageMIwoc (not averageMI): the everse formula has 3 factors (Halstead,
        # complexity, LOC), no comment bonus. It seems to match the description 
        # in the indicator better than averageMI.

        miwoc = report.get("averageMIwoc", 0)
        ok = miwoc >= 65  # ast-metrics' own convention for "easy to maintain"  

        # 85-100 -> easy to maintain
        # 65-84 -> moderate maintainability
        # <65 -> hard to maintain

        return CheckResult(
            process="Measures maintainability index using ast-metrics.",
            status_id="schema:CompletedActionStatus",
            output="true" if ok else "false",
            evidence=f"Average maintainability index (without comment weighting): {miwoc:.1f}/100 "
                f"(threshold: 65 -> moderate-or-better maintainability; below 65 is considered hard to maintain).",
            success=ok,
        )