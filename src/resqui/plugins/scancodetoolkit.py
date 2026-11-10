import json
import os
import subprocess

from pathlib import Path
from resqui.plugins.base import IndicatorPlugin
from resqui.executors import PythonExecutor
from resqui.core import CheckResult
from resqui.workspace import create_workspace

TIMEOUT_SECONDS = 1800

# Defalut scancode-toolkit timeout
PER_FILE_TIMEOUT_SECONDS = 120

DOC_EXTENSIONS = {".md", ".rst", ".txt", ".adoc", ".tex", ".html", ".htm", ".org"}
# REUSE metadata files: they declare licenses for other files, they are not
# files that need a license themselves.
REUSE_METADATA_FILES = {"REUSE.toml", ".reuse/dep5"}


def _file_category(entry):
    """Classify a ScanCode file entry as code, documentation, media or other."""
    if entry.get("is_source") or entry.get("is_script"):
        return "code"
    if entry.get("is_readme") or (entry.get("extension") or "").lower() in DOC_EXTENSIONS:
        return "documentation"
    if entry.get("is_media"):
        return "media"
    return "other"


class ScanCodeToolkit(IndicatorPlugin):
    """License detection for every file of a repository with
    [ScanCode Toolkit](https://github.com/aboutcode-org/scancode-toolkit).

    Languages: language-independent.
    """

    name = "ScanCodeToolkit"
    version = "32.5.0"
    # Provisional: ScanCode Toolkit is not registered in the TechRadar yet.
    id = "https://w3id.org/everse/tools/scancode-toolkit"
    indicators = [ 
        "has_license",
        "software_has_license_for_file_types"
    ]
    requires = []

    def __init__(self, context):
        self.context = context
        self.executor = PythonExecutor()
        self.executor.install(f"scancode-toolkit=={self.version}")
        # pluggy>=1.6 breaks scancode's plugin loading ("did not find any
        # 'pre_scan' hooks"), so pin it to a compatible version.
        self.executor.install("pluggy<1.6")
        self._cache = {}

    def execute(self, url, branch=None):
        """Clone the repository, run ScanCode on it and return its JSON report.

        On failure, returns a dict with an "error" key instead.
        """
        cache_key = (url, branch)
        if cache_key in self._cache:
            return self._cache[cache_key]

        scancode_bin = f"{self.executor.temp_dir}/bin/scancode"
        with create_workspace(prefix="resqui-scancode-") as ws:
            try:
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
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                report = {"error": f"Could not clone {url} ({branch}): {e}"}
                self._cache[cache_key] = report
                return report

            # Write the report outside the scanned tree so it isn't scanned.
            report_path = Path(f"{ws.local_path}-scancode.json")
            try:
                result = subprocess.run(
                    [
                        scancode_bin,
                        "--license",
                        "--info",
                        "--classify",
                        "--summary",
                        "--strip-root",
                        "--processes", str(max(1, (os.cpu_count() or 2) - 1)),
                        "--timeout", str(PER_FILE_TIMEOUT_SECONDS),
                        "--ignore", ".git/*",
                        "--json", str(report_path),
                        ".",
                    ],
                    cwd=ws.local_path,
                    timeout=TIMEOUT_SECONDS,
                    capture_output=True,
                    text=True,
                )
                if report_path.exists():
                    report = json.loads(report_path.read_text())
                else:
                    report = {
                        "error": "ScanCode did not produce a report "
                        f"(return code {result.returncode}): {result.stderr.strip()[-1000:]}"
                    }
            except subprocess.TimeoutExpired:
                report = {"error": f"ScanCode timed out after {TIMEOUT_SECONDS}s."}
            except json.JSONDecodeError as e:
                report = {"error": f"Could not parse the ScanCode report: {e}"}
            finally:
                report_path.unlink(missing_ok=True)

        self._cache[cache_key] = report
        return report

    def has_license(self, url, branch=None):
        process = (
            "Runs ScanCode Toolkit license detection with its codebase summary, "
            "which derives the license declared for the whole project from its "
            "top-level key files (e.g. LICENSE, README, package manifests). "
            "The check passes if a declared license is found."
        )
        report = self.execute(url, branch)

        if "error" in report:
            return CheckResult(
                process=process,
                status_id="schema:FailedActionStatus",
                output="error",
                evidence=report["error"],
                success=False,
            )

        summary = report.get("summary")
        if not summary:
            return CheckResult(
                process=process,
                status_id="schema:FailedActionStatus",
                output="error",
                evidence="The ScanCode report has no codebase summary.",
                success=False,
            )

        clarity = summary.get("license_clarity_score") or {}
        success = bool(clarity.get("declared_license"))
        score = clarity.get("score", 0)

        if success:
            key_files = sorted(
                f"{f['path']} ({f['detected_license_expression_spdx']})"
                for f in report.get("files", [])
                if f.get("is_key_file") and f.get("detected_license_expression_spdx")
            )
            evidence = (
                f"Declared license: {summary.get('declared_license_expression')}, "
                f"found in: {', '.join(key_files) or 'key files'}. "
                f"License clarity score: {score}/100."
            )
        else:
            evidence = "No declared license found in the project's key files."

        return CheckResult(
            process=process,
            status_id="schema:CompletedActionStatus",
            output="true" if success else "false",
            evidence=evidence,
            success=success,
            raw_value=str(score),
            threshold="Passes if a declared license is found in the project's key files.",
        )


    def software_has_license_for_file_types(self, url, branch=None):
        process = (
            "Runs ScanCode Toolkit license detection on every file. The plugin then "
            "groups files by type (code, documentation, media, other) and, following "
            "the REUSE specification, also counts a file as licensed when it has a "
            "'<file>.license' companion file. Legal files, empty files and REUSE "
            "metadata files are not counted. ScanCode does not read REUSE.toml or "
            ".reuse/dep5, so licenses declared there are not taken into account. "
            "Reference: https://reuse.software/spec/"
        )
        report = self.execute(url, branch)

        if "error" in report:
            return CheckResult(
                process=process,
                status_id="schema:FailedActionStatus",
                output="error",
                evidence=report["error"],
                success=False,
            )

        files = [f for f in report.get("files", []) if f.get("type") == "file"]
        licensed_paths = {
            f["path"] for f in files if f.get("detected_license_expression")
        }

        categories = {}
        for entry in files:
            path = entry["path"]
            if (
                entry.get("is_legal")
                or not entry.get("size")
                or path.endswith(".license")
                or path in REUSE_METADATA_FILES
            ):
                continue
            has_license = path in licensed_paths or f"{path}.license" in licensed_paths
            category = _file_category(entry)
            total, licensed = categories.get(category, (0, 0))
            categories[category] = (total + 1, licensed + has_license)

        total = sum(t for t, _ in categories.values())
        if total == 0:
            return CheckResult(
                process=process,
                status_id="schema:CompletedActionStatus",
                output="indeterminate",
                evidence="No files to check were found in the repository.",
                success=True,
            )

        licensed = sum(lic for _, lic in categories.values())
        coverage = 100.0 * licensed / total
        success = licensed == total
        breakdown = ", ".join(
            f"{name}: {lic}/{t}" for name, (t, lic) in sorted(categories.items())
        )
        expressions = sorted(
            {
                f["detected_license_expression_spdx"]
                for f in files
                if f.get("detected_license_expression_spdx")
            }
        )
        evidence = (
            f"{licensed}/{total} files ({coverage:.1f}%) have license information "
            f"({breakdown}). Licenses found: {', '.join(expressions) or 'none'}."
        )

        return CheckResult(
            process=process,
            status_id="schema:CompletedActionStatus",
            output="true" if success else "false",
            evidence=evidence,
            success=success,
            raw_value=f"{coverage:.1f}",
            threshold="100",
        )
