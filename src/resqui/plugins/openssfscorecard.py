import json
import subprocess

from resqui.plugins.base import IndicatorPlugin
from resqui.core import CheckResult


class OpenSSFScorecard(IndicatorPlugin):
    name = "OpenSSF Scorecard"
    id = "https://github.com/ossf/scorecard"
    version = "v5.1.1"
    indicators = [
        "has_ci_tests",
        "human_code_review_requirement",
        "has_published_package",
    ]

    def __init__(self, context):
        self.context = context
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

        cmd = [
            "docker",
            "run",
            "--rm",
            "-e",
            f"GITHUB_AUTH_TOKEN={self.context.github_token}",
            f"gcr.io/openssf/scorecard:{self.version}",
            "--repo",
            url,
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
                return check["score"]
        raise ValueError(f"Check '{check_name}' not found in results.")

    def has_ci_tests(self, url, branch_hash_or_tag):
        results = self.execute(url, branch_hash_or_tag)
        score = self.get_score(results, "CI-Tests")
        if score >= 5:
            output = "true"
            evidence = f"CI-Tests score is 5 or higher ({score})."
            success = True
        else:
            output = "false"
            evidence = f"CI-Tests score is less than 5 ({score})."
            success = False

        return CheckResult(
            process="Calculates the CI-Tests score.",
            status_id="Pass" if success else "Fail",
            output=output,
            evidence=evidence,
            success=success,
        )

    def human_code_review_requirement(self, url, branch_hash_or_tag):
        results = self.execute(url, branch_hash_or_tag)
        score = self.get_score(results, "Code-Review")

        if score >= 5:
            output = "true"
            evidence = f"Code-Review score is 5 or higher ({score})."
            success = True
        else:
            output = "false"
            evidence = f"Code-Review score is less than 5 ({score})."
            success = False

        return CheckResult(
            process="Calculates the Code-Review score.",
            status_id="Pass" if success else "Fail",
            output=output,
            evidence=evidence,
            success=success,
        )

    def has_published_package(self, url, branch_hash_or_tag):
        results = self.execute(url, branch_hash_or_tag)
        score = self.get_score(results, "Packaging")

        if score >= 5:
            output = "true"
            evidence = f"Packaging score is 5 or higher ({score})."
            success = True
        else:
            output = "false"
            evidence = f"Packaging score is less than 5 ({score})."
            success = False

        return CheckResult(
            process="Calculates the Packaging score.",
            status_id="Pass" if success else "Fail",
            output=output,
            evidence=evidence,
            success=success,
        )
