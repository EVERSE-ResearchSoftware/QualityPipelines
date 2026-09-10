import json
import subprocess
import os

from pathlib import Path
from resqui.plugins.base import IndicatorPlugin
from resqui.executors import PythonExecutor
from resqui.core import CheckResult
from resqui.workspace import create_workspace


class PySCN(IndicatorPlugin):
    name = "PySCN"
    version = "1.30.0"
    id = "https://w3id.org/everse/tools/pyscn"
    indicators = [
        "cyclomatic_complexity_ok",
        "code_duplication_ok",
        "coupling_between_objects_ok",
        "internal_cohesion_ok",
    ]

    def __init__(self, context):
        self.context = context
        self.executor = PythonExecutor()
        self.executor.install(f"pyscn=={self.version}")
        self._cache = {}

    def execute(self, url, branch):
        cache_key = (url, branch)
        if cache_key in self._cache:
            return self._cache[cache_key]
        pyscn_bin = f"{self.executor.temp_dir}/bin/pyscn"
        with create_workspace(prefix="resqui-pyscn-") as ws:
            subprocess.run(["git", "clone", url, ws.local_path], check=True,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(
                [pyscn_bin, "analyze", "--json", "."],
                check=True,
                cwd=ws.local_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            report_dir = os.path.join(ws.local_path, ".pyscn", "reports")
            json_files = sorted(Path(report_dir).glob("*.json"), key=os.path.getmtime)
            report_path = json_files[-1]
            report = json.loads(report_path.read_text())
        self._cache[cache_key] = report
        return report

    def cyclomatic_complexity_ok(self, url, branch):
        summary = self.execute(url, branch)["summary"]
        ok = summary["average_complexity"] <= 4
        return CheckResult(
            process="Measures cyclomatic complexity of Python functions and classes",
            status_id="schema:CompletedActionStatus",
            output="true" if ok else "false",
            evidence=f"Average complexity {summary['average_complexity']}; "
                     f"{summary['high_complexity_count']} functions/classes exceed complexity 10.",
            success=ok,
        )

    def code_duplication_ok(self, url, branch):
        summary = self.execute(url, branch)["summary"]
        ok = summary["code_duplication_percentage"] <= 40
        return CheckResult(
            process="Detects duplicated code in the Python project",
            status_id="schema:CompletedActionStatus",
            output="true" if ok else "false",
            evidence=f"Percentage of duplication: {summary['code_duplication_percentage']}%; "
                     f"{summary['total_clones']} duplicated fragments.",
            success=ok,
        )

    def coupling_between_objects_ok(self, url, branch):
        summary = self.execute(url, branch)["summary"]
        ok = summary["average_coupling"] <= 4
        return CheckResult(
            process="Measures the coupling between objects (CBO) of the Python classes",
            status_id="schema:CompletedActionStatus",
            output="true" if ok else "false",
            evidence=f"CBO average {summary['average_coupling']}; "
                     f"{summary['high_coupling_classes']} classes exceed CBO 7.",
            success=ok,
        )

    def internal_cohesion_ok(self, url, branch):
        summary = self.execute(url, branch)["summary"]
        ok = summary["high_lcom_classes"] <= 4
        return CheckResult(
            process="Measures internal cohesion (LCOM4) of Python classes",
            status_id="schema:CompletedActionStatus",
            output="true" if ok else "false",
            evidence=f"LCOM4 average {summary['average_lcom']}; "
                     f"{summary['high_lcom_classes']} classes exceed LCOM4 5.",
            success=ok,
        )