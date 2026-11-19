import json
import subprocess

from pathlib import Path
from resqui.plugins.base import IndicatorPlugin
from resqui.executors import PythonExecutor
from resqui.core import CheckResult
from resqui.workspace import create_workspace

TIMEOUT_SECONDS = 600
MIN_MAINTAINABILITY_INDEX = 65  # ast-metrics' convention: >=65 is moderate-or-better

class ASTMetrics(IndicatorPlugin):
    """Static code metrics with [ast-metrics](https://ast-metrics.dev).

    Languages: Python, Go, PHP, TypeScript, Rust, Java, C#.
    """

    name = "ASTMetrics"
    version = "0.43.1"
    id = "https://w3id.org/everse/tools/ast-metrics"  
    indicators = ["maintainability_index_ok"]
    requires = []

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
        ok = miwoc >= MIN_MAINTAINABILITY_INDEX
        # 85-100 -> easy to maintain
        # 65-84 -> moderate maintainability
        # <65 -> hard to maintain

        return CheckResult(
            process="Measures maintainability index using ast-metrics.",
            status_id="schema:CompletedActionStatus",
            output="true" if ok else "false",
            evidence=f"Average maintainability index (without comment weighting): {miwoc:.1f}/100 "
                f"(threshold: {MIN_MAINTAINABILITY_INDEX} -> moderate-or-better maintainability; "
                f"below {MIN_MAINTAINABILITY_INDEX} is considered hard to maintain).",
            success=ok,
            raw_value=f"{miwoc:.1f}",
            threshold=str(MIN_MAINTAINABILITY_INDEX),
        )