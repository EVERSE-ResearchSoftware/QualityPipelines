import json
import subprocess

from pathlib import Path
from resqui.plugins.base import IndicatorPlugin
from resqui.executors import PythonExecutor
from resqui.core import CheckResult
from resqui.workspace import create_workspace
TIMEOUT_SECONDS = 600 

class Pylint(IndicatorPlugin):
    name = "Pylint"
    version = "4.0.8"
    id = "https://w3id.org/everse/tools/pylint" 
    indicators = ["code_smells_ok"]

    def __init__(self, context):
        self.context = context
        self.executor = PythonExecutor()
        self.executor.install(f"pylint=={self.version}")
        self._cache = {}

    def execute(self, url, branch=None):
        cache_key = (url, branch)
        if cache_key in self._cache:
            return self._cache[cache_key]

        pylint_bin = f"{self.executor.temp_dir}/bin/pylint"

        with create_workspace(prefix="resqui-pylint-") as ws:
            subprocess.run(["git", "clone", "--", url, ws.local_path], check=True,
                            timeout=TIMEOUT_SECONDS,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if branch:
                subprocess.run(["git", "checkout", branch], check=True, cwd=ws.local_path,
                                timeout=TIMEOUT_SECONDS,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            repo_path = Path(ws.local_path)
            src_dirs = [d for d in repo_path.rglob("src") if d.is_dir() and ".git" not in d.parts]
            search_base = src_dirs[0] if src_dirs else repo_path

            ignored_dirs = {".git", "venv", ".venv", "__pycache__", "build", "dist",
                             ".egg-info", "node_modules"}

            all_files = [
                        f for f in search_base.rglob("*") 
                        if f.is_file() and not any(part in ignored_dirs for part in f.parts)
                    ]

            total_files = len(all_files)

            if total_files == 0:
                report = {
                    "skippable": True,
                    "reason": "The repository contains no source files.",
                }

                self._cache[cache_key] = report
                return report

            python_files = [
                f for f in all_files
                if f.suffix == ".py"
            ]

            python_ratio = len(python_files) / total_files

            print(f"Total files: {total_files}")
            # print(f"Python files: {len(python_files)}")
            # print(f"Python ratio: {python_ratio:.2%}")

            if python_ratio < 0.20:
                report = {
                    "skippable": True,
                    "reason": (
                        "Less than 20% of the repository files are Python files."
                    ),
                }

                self._cache[cache_key] = report
                return report

            report = {"skippable": False}
            report["lines_of_code"] = sum(
                len(f.read_text(errors="ignore").splitlines())
                for f in python_files
            )

            rel_files = [
                str(f.relative_to(repo_path))
                for f in python_files
            ]

            # Pylint may return a non-zero exit code when it finds messages,
            # so check=True is intentionally not used here.

            result = subprocess.run(
                [pylint_bin, "--output-format=json2", *rel_files],
                cwd=ws.local_path,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
            )

            try:
                pylint_output = json.loads(result.stdout)
                report["statistics"] = pylint_output.get("statistics", {})
                report["pylint_parse_error"] = False
            except json.JSONDecodeError:
                report["statistics"] = {}
                report["pylint_parse_error"] = True

            report["pylint_returncode"] = result.returncode
            report["pylint_stderr"] = (result.stderr or "").strip()[-300:]

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

    def code_smells_ok(self, url, branch=None):
        report = self.execute(url, branch)

        if report["skippable"]:
            return self.handle_skip(
                "Measures code smell ratio using pylint."
            )

        if report.get("pylint_parse_error"):
            return CheckResult(
                process="Measures code smell ratio using pylint.",
                status_id="schema:CompletedActionStatus",
                output="indeterminate",
                evidence=(
                    f"Pylint exited with code {report.get('pylint_returncode', '?')}: "
                    f"{report.get('pylint_stderr') or 'no parseable output'}."
                ),
                success=True,
            )
        counts = report["statistics"].get("messageTypeCount", {})
        # "Code smell" = design/maintainability problems (refactor + convention);
        # warning/error/fatal are excluded since they concern correctness rather than design.
        code_smells = counts.get("refactor", 0) + counts.get("convention", 0)
        loc = report["lines_of_code"]

        ratio = (code_smells / loc) * 1000 if loc else 0
        ok = ratio < 50 

        return CheckResult(
            process="Measures code smell ratio using pylint.",
            status_id="schema:CompletedActionStatus",
            output="true" if ok else "false",
            evidence=f"{code_smells} code smells (refactor: {counts.get('refactor', 0)}, "
                    f"convention: {counts.get('convention', 0)}) over {loc} lines of code "
                    f"= {ratio:.2f} per 1000 LOC (threshold: 50).",
            success=ok,
        )