import json
import subprocess
import ast

from pathlib import Path
from resqui.tools import normalized
from resqui.plugins.base import IndicatorPlugin
from resqui.executors import PythonExecutor
from resqui.core import CheckResult
from resqui.workspace import create_workspace

TIMEOUT_SECONDS = 600
FAIL_UNDER = 80.0  # interrogate default. We can modify if needed, but we should be consistent with the tool's default behavior.
EXCLUDED_DIRS = ("build", "dist", "node_modules")


class Interrogate(IndicatorPlugin):
    name = "Interrogate"
    version = "1.7.0"
    id = "https://w3id.org/everse/tools/interrogate"
    indicators = ["code_documentation_coverage_ok"]

    def __init__(self, context):
        self.context = context
        self.executor = PythonExecutor()
        self.executor.install(f"interrogate=={self.version}")
        self._cache = {}

    def execute(self, url, branch=None):
        cache_key = (url, branch)
        if cache_key in self._cache:
            return self._cache[cache_key]

        with create_workspace(prefix="resqui-interrogate-") as ws:
            repo_path = Path(ws.local_path)

            subprocess.run(
                ["git", "clone", "--", url, ws.local_path],
                check=True,
                timeout=TIMEOUT_SECONDS,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if branch:
                subprocess.run(
                    ["git", "checkout", branch],
                    check=True,
                    cwd=ws.local_path,
                    timeout=TIMEOUT_SECONDS,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            if not any(repo_path.rglob("*.py")):
                report = {"status": "no_python"}
                self._cache[cache_key] = report
                return report

            excluded = tuple(str(repo_path / d) for d in EXCLUDED_DIRS)
            script = normalized(
                f"""
                import json
                from interrogate import coverage

                cov = coverage.InterrogateCoverage(
                    paths=[{str(repo_path)!r}],
                    excluded={excluded!r},
                )
                results = cov.get_coverage()
                print(json.dumps({{
                    "total": results.total,
                    "covered": results.covered,
                    "missing": results.missing,
                    "percentage": results.perc_covered,
                }}))
                """
            )
            result = self.executor.execute(script)
            # print(result.stdout.strip(), end=" ")

            if result.returncode != 0 or not result.stdout.strip():
                culprit = None
                for path in repo_path.rglob("*.py"):
                    try:
                        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                    except SyntaxError as exc:
                        culprit = f"{path.relative_to(repo_path)}:{exc.lineno}: {exc.msg}"
                        break
                report = {
                    "status": "error",
                    "message": culprit or (result.stderr or "").strip()[:500],
                }
                self._cache[cache_key] = report
                return report

            report = json.loads(result.stdout)
            report["status"] = "ok"

        self._cache[cache_key] = report
        return report

    def code_documentation_coverage_ok(self, url, branch=None):
        report = self.execute(url, branch)

        if report.get("status") != "ok":
            return CheckResult(
                process="Measures docstring coverage of Python code with interrogate.",
                status_id="schema:CompletedActionStatus",
                output="indeterminate",
                evidence=report.get("message", "No Python code found to measure."),
                success=True,
            )

        ok = report["percentage"] >= FAIL_UNDER
        evidence = (
            f"Docstring coverage: {report['percentage']:.1f}% "
            f"({report['covered']}/{report['total']} documented objects; "
            f"threshold: {FAIL_UNDER:.1f}%; every Python file in the "
            "repository is measured (package, tests and vendored code "
            "alike) covering all functions/methods/classes/modules, "
            "including private ones. Markdown (.md) documentation is "
            "assessed by the software_has_documentation indicator)."
        )
        return CheckResult(
            process="Measures docstring coverage of Python code with interrogate.",
            status_id="schema:CompletedActionStatus",
            output="true" if ok else "false",
            evidence=evidence,
            success=ok,
        )