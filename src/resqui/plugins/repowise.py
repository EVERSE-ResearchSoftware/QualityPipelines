import json
import subprocess

from pathlib import Path
from resqui.plugins.base import IndicatorPlugin
from resqui.executors import PythonExecutor
from resqui.core import CheckResult
from resqui.workspace import create_workspace


class Repowise(IndicatorPlugin):
    """Measures code churn with [repowise](https://w3id.org/everse/tools/repowise).

    A check passes while fewer than 40% of the files with git-history data are
    flagged by repowise as hotspots. This cutoff is provisional and pending
    agreement with the EVERSE team; every result reports it in `threshold`
    together with the measured `raw_value`.
    """
    name = "Repowise"
    version = "0.50.0"
    id = "https://w3id.org/everse/tools/repowise"
    indicators = ["code_churn_ok"]
    TIMEOUT_SECONDS = 600 
    MAX_HOTSPOT_PERCENT = 40
    
    def __init__(self, context):
        self.context = context
        self.executor = PythonExecutor()
        self.executor.install(f"repowise=={self.version}")
        self._cache = {}


    def execute(self, url, branch=None):
        cache_key = (url, branch)
        if cache_key in self._cache:
            return self._cache[cache_key]

        repowise_bin = f"{self.executor.temp_dir}/bin/repowise"

        with create_workspace(prefix="resqui-repowise-") as ws:
            subprocess.run(["git", "clone", "--", url, ws.local_path], check=True,
                            timeout=self.TIMEOUT_SECONDS,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if branch:
                subprocess.run(["git", "checkout", branch], check=True, cwd=ws.local_path,
                                timeout=self.TIMEOUT_SECONDS,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            def git_commit_count(*rev_args):
                try:
                    result = subprocess.run(
                        ["git", "rev-list", "--count", *rev_args],
                        capture_output=True, text=True, cwd=ws.local_path,
                        timeout=self.TIMEOUT_SECONDS, check=True,
                    )
                except subprocess.CalledProcessError as exc:
                    stderr = (exc.stderr or "").lower()
                    if "head" in stderr and any(
                        phrase in stderr
                        for phrase in ("bad revision", "unknown revision", "ambiguous argument")
                    ):
                        return 0
                    raise
                return int(result.stdout.strip() or 0)

            commits_total = git_commit_count("HEAD")
            commits_90d = git_commit_count("--since=90 days ago", "HEAD") if commits_total else 0

            targets = {}
            if commits_total:
                subprocess.run([repowise_bin, "init", "--no-prose", "-y"], check=True,
                                cwd=ws.local_path, timeout=self.TIMEOUT_SECONDS,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                repo_path = Path(ws.local_path)
                ignored_dirs = {".git", "venv", ".venv", "__pycache__", "build", "dist",
                                ".egg-info", ".repowise"}
                all_files = [f for f in repo_path.rglob("*")
                            if f.is_file() and not any(part in ignored_dirs for part in f.parts)]

                # Repowise silently truncates targets above a certain number in a single call,
                # (observed at 40 targets on the somef repository), so we batch them in
                # conservative groups of 30.
                batch_size = 30

                for i in range(0, len(all_files), batch_size):
                    batch = all_files[i:i + batch_size]
                    batch_args = []
                    for f in batch:
                        batch_args += ["--target", str(f.relative_to(repo_path))]
                    result = subprocess.run(
                        [repowise_bin, "risk", *batch_args, "--format", "json", "--full"],
                        check=True, cwd=ws.local_path, capture_output=True, text=True,
                        timeout=self.TIMEOUT_SECONDS,
                    )
                    targets.update(json.loads(result.stdout).get("targets", {}))

            report = {
                "commits_total": commits_total,
                "commits_90d": commits_90d,
                "targets": targets
            }

        self._cache[cache_key] = report
        return report


    def code_churn_ok(self, url, branch=None):
        report = self.execute(url, branch)
        
        if report["commits_total"] == 0:
            return CheckResult(
                process="Measures code churn over time using repowise",
                status_id="schema:CompletedActionStatus",
                output="indeterminate",
                evidence="Repository has no commits yet (empty repository).",
                success=True,
            )

        targets = report["targets"]
        tracked = {k: t for k, t in targets.items() if t.get("change_magnitude") is not None}
        total = len(tracked)

        if total == 0:
            return CheckResult(
                process="Measures code churn over time using repowise",
                status_id="schema:CompletedActionStatus",
                output="indeterminate",
                evidence=f"No files with git history data indexed by repowise "
                        f"({report['commits_total']} total commits, {report['commits_90d']} in the last 90 days).",
                success=True,
            )

        hotspots = sum(1 for t in tracked.values() if t.get("is_hotspot", False))
        total_lines = sum(
            t["change_magnitude"].get("lines_added_90d", 0) + t["change_magnitude"].get("lines_deleted_90d", 0)
            for t in tracked.values()
        )

        hotspot_files = sorted(
        (
            {
                "file": k,
                "hotspot_score": t.get("hotspot_score", 0),
                "lines_added_90d": t["change_magnitude"].get("lines_added_90d", 0),
                "lines_deleted_90d": t["change_magnitude"].get("lines_deleted_90d", 0),
            }
            for k, t in tracked.items() if t.get("is_hotspot", False)
        ),
        key=lambda x: -x["hotspot_score"],
    )
        pct = (hotspots / total * 100) if total else 0
        # ok = pct < 40 # provisional threshold, to be discussed with the team.
        ok = pct < self.MAX_HOTSPOT_PERCENT

        return CheckResult(
            process="Measures code churn over time using repowise",
            status_id="schema:CompletedActionStatus",
            output="true" if ok else "false",
            evidence=(
                f"{hotspots}/{total} files flagged as hotspots by repowise ({pct:.1f}%) among files "
                f"with git-history data; the check passes while that share is below "
                f"{self.MAX_HOTSPOT_PERCENT}% (provisional threshold, pending team agreement). "
                f"{total} of {len(targets)} total files are indexed (repowise does not track lock files, "
                f"configs or other non-source files); {total_lines} lines changed in 90 days across those "
                f"tracked files; {report['commits_90d']} commits in the last 90 days "
                f"({report['commits_total']} total)."
            ),
            success=ok,
            raw_value=json.dumps(hotspot_files, separators=(",", ":")),
            threshold=str(self.MAX_HOTSPOT_PERCENT),
        )