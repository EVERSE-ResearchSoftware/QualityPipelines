import json
import subprocess
from resqui.plugins.base import IndicatorPlugin, PluginInitError
from resqui.core import CheckResult


class OpenSSFScorecard(IndicatorPlugin):
    name = "OpenSSF Scorecard"
    id = "https://github.com/ossf/scorecard"
    version = "v5.4.0"
    indicators = [
        "has_ci_tests",
        "human_code_review_requirement",
        "has_published_package",
        "dependency_management",
        "uses_fuzzing",
        "no_critical_vulnerability",
        "static_analysis_common_vulnerabilities",
        "project_is_active"
    ]

    def __init__(self, context):
        self.context = context
        if not context.github_token:
            raise PluginInitError("missing GITHUB_ACTION_TOKEN")
        self.instantiate()
        self._cache = {}

    def instantiate(self):
        try:
            subprocess.run(
                ["docker", "pull", f"gcr.io/openssf/scorecard:{self.version}"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error pulling OpenSSF Scorecard image: {e}")
            raise

    def execute(self, url, commit_hash):
        cache_key = (url, commit_hash)
        if cache_key in self._cache:
            return self._cache[cache_key]

        url = url[:-4] if url.endswith(".git") else url
        
        check_values = ["CI-Tests", "SAST", "Maintained", "Fuzzing", "Dependency-Update-Tool", "Vulnerabilities", "Code-Review", "Packaging"]
        check_args = [arg for check in check_values for arg in ("--checks", check)]

        cmd = [
            "docker",
            "run",
            "--rm", # added --rm argument for eliminate the docker container after its processing
            "-e",
            f"GITHUB_AUTH_TOKEN={self.context.github_token}",
            f"gcr.io/openssf/scorecard:{self.version}",
            *check_args,
            "--show-details",
            "--repo",
            url,
            # TODO: commit hash is not used currently
            # "--commit",
            ## commit_hash,
            "--format",
            "json",
        ]

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if r.stdout:
                out = json.loads(r.stdout)
                self._cache[cache_key] = out
                return out
            else:
                raise ValueError("No output received from Scorecard.")
        except subprocess.CalledProcessError as e:
            print("Scorecard error output:")
            print(e.stderr)
            raise
        except json.JSONDecodeError:
            print("JSON output not valid:")
            print(r.stdout)
            raise

    def get_score(self, results, check_name):
        checks = results["checks"]
        if not checks:
            raise ValueError("No checks found in results.")
        for check in checks:
            if check["name"] == check_name:
                return check
        raise ValueError(f"Check '{check_name}' not found in results.")

    def has_ci_tests(self, url, branch_hash_or_tag):
        results = self.execute(url, branch_hash_or_tag)
        check = self.get_score(results, "CI-Tests")
        if check["score"] > 0:
            output = "true"
            evidence = check["reason"]
            success = True
        else:
            output = "false"
            evidence = check["reason"]
            success = False

        return CheckResult(
            process="Checks if there are PRs checked by CI-Tests",
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )

    def human_code_review_requirement(self, url, branch_hash_or_tag):
        results = self.execute(url, branch_hash_or_tag)
        check = self.get_score(results, "Code-Review")

        if check["score"] >= 5:
            output = "true"
            evidence = check["reason"]
            success = True
        else:
            output = "false"
            evidence = check["reason"]
            success = False

        return CheckResult(
            process="Checks if at least half of the changesets in the repository are approved",
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )

    def has_published_package(self, url, branch_hash_or_tag):
        results = self.execute(url, branch_hash_or_tag)
        check = self.get_score(results, "Packaging")

        if check["score"] > 0:
            output = "true"
            evidence = check["details"]
            success = True
        else:
            output = "false"
            evidence = check["details"]
            success = False

        return CheckResult(
            process="Checks if there are workflows for package releasing (i.e PyPI)",
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )

    def project_is_active(self, url, branch_hash_or_tag):
        results = self.execute(url, branch_hash_or_tag)
        check = self.get_score(results, "Maintained")
        if check["score"] >= 3:
            output = "true"
            evidence = check["reason"]
            success = True
        else:
            output = "false"
            evidence = check["reason"]
            success = False

        return CheckResult(
            process="Checks if there are commits and issue activity in the last 90 days",
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )
        
    def static_analysis_common_vulnerabilities(self, url, branch_hash_or_tag):
        results = self.execute(url, branch_hash_or_tag)
        check = self.get_score(results, "SAST")
        if check["score"] > 0:
            output = "true"
            evidence = check["details"]
            success = True
        else:
            output = "false"
            evidence = check["details"]
            success = False

        return CheckResult(
            process="Checks if there are commits checked with a SAST tool",
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )
        
    def dependency_management(self, url, branch_hash_or_tag):
        success=False
        results = self.execute(url, branch_hash_or_tag)
        check = self.get_score(results, "Dependency-Update-Tool")
        if check["score"] > 0:
            output = "true"
            evidence = check["details"]
            success = True
        else:
            output = "false"
            evidence = check["details"]
            success = False

        return CheckResult(
            process="Checks if there is a dependency update tool in the repository",
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )
        
    def no_critical_vulnerability(self, url, branch_hash_or_tag):
        success=False
        results = self.execute(url, branch_hash_or_tag)
        check = self.get_score(results, "Vulnerabilities")
        if check["score"] >= 7:
            output = "true"
            evidence = check["details"]
            success = True
        else:
            output = "false"
            evidence = check["details"]

        return CheckResult(
            process="Checks if there are vulnerabilities in the repository",
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )
        
    def uses_fuzzing(self, url, branch_hash_or_tag):
        success=False
        results = self.execute(url, branch_hash_or_tag)
        check = self.get_score(results, "Fuzzing")
        if check["score"] > 0:
            output = "true"
            evidence = check["details"]
            success = True
        else:
            output = "false"
            evidence = check["details"]
            success = False

        return CheckResult(
            process="Checks if the project integrates fuzzing",
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )