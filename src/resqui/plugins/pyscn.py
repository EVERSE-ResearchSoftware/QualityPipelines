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

    def execute(self, url, branch=None):
        cache_key = (url, branch)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        pyscn_bin = f"{self.executor.temp_dir}/bin/pyscn"
        
        with create_workspace(prefix="resqui-pyscn-") as ws:
            repo_path = Path(ws.local_path)
            
            subprocess.run(
                ["git", "clone", url, ws.local_path],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            if branch:
                subprocess.run(
                    ["git", "checkout", branch],
                    check=True,
                    cwd=ws.local_path,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            src_dirs = [d for d in repo_path.rglob("src") if d.is_dir() and ".git" not in d.parts]
            search_base = src_dirs[0] if src_dirs else repo_path
            ignored_dirs = {".git", "venv", ".venv", "__pycache__", "build", "dist", ".egg-info"}

            all_files = [
                f for f in search_base.rglob("*")
                if f.is_file() and not any(part in ignored_dirs for part in f.parts)
            ]
            
            total_files = len(all_files)
            if total_files == 0:
                report = {
                    "skippable": True,
                    "reason": "El repositorio o directorio fuente está vacío."
                }
                self._cache[cache_key] = report
                return report

            python_files = [f for f in all_files if f.suffix == ".py"]
            python_ratio = len(python_files) / total_files

            if python_ratio < 0.20:
                report = {
                    "skippable": True,
                }
                self._cache[cache_key] = report
                return report

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
            report["skippable"] = False

        self._cache[cache_key] = report
        return report

    def handle_skip(self, process):
        return CheckResult(
            process=process,
            status_id="schema:CompletedActionStatus",
            output="indeterminate",
            evidence="The repository must contain at least 20% of files with the .py extension.",
            success=True,
        )

    def cyclomatic_complexity_ok(self, url, branch=None):
        report = self.execute(url, branch)
        if report.get("skippable"):
            return self.handle_skip("Measures cyclomatic complexity of Python functions and classes")

        summary = report["summary"]
        ok = summary["average_complexity"] <= 4
        return CheckResult(
            process="Measures cyclomatic complexity of Python functions and classes",
            status_id="schema:CompletedActionStatus",
            output="true" if ok else "false",
            evidence=f"Average complexity {summary['average_complexity']}; "
                     f"{summary['high_complexity_count']} functions/classes exceed complexity 10.",
            success=ok,
        )

    def code_duplication_ok(self, url, branch=None):
        report = self.execute(url, branch)
        if report.get("skippable"):
            return self.handle_skip("Detects duplicated code in the Python project")

        summary = report["summary"]
        ok = summary["code_duplication_percentage"] <= 40
        return CheckResult(
            process="Detects duplicated code in the Python project",
            status_id="schema:CompletedActionStatus",
            output="true" if ok else "false",
            evidence=f"Percentage of duplication: {summary['code_duplication_percentage']}%; "
                     f"{summary['total_clones']} duplicated fragments.",
            success=ok,
        )

    def coupling_between_objects_ok(self, url, branch=None):
        report = self.execute(url, branch)
        if report.get("skippable"):
            return self.handle_skip("Measures the coupling between objects (CBO) of the Python classes")

        summary = report["summary"]
        ok = summary["average_coupling"] <= 4
        return CheckResult(
            process="Measures the coupling between objects (CBO) of the Python classes",
            status_id="schema:CompletedActionStatus",
            output="true" if ok else "false",
            evidence=f"CBO average {summary['average_coupling']}; "
                     f"{summary['high_coupling_classes']} classes exceed CBO 7.",
            success=ok,
        )

    def internal_cohesion_ok(self, url, branch=None):
        report = self.execute(url, branch)
        if report.get("skippable"):
            return self.handle_skip("Measures internal cohesion (LCOM4) of Python classes")

        summary = report["summary"]
        ok = summary["high_lcom_classes"] <= 4
        return CheckResult(
            process="Measures internal cohesion (LCOM4) of Python classes",
            status_id="schema:CompletedActionStatus",
            output="true" if ok else "false",
            evidence=f"LCOM4 average {summary['average_lcom']}; "
                     f"{summary['high_lcom_classes']} classes exceed LCOM4 5.",
            success=ok,
        )