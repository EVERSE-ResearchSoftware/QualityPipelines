import os
import platform
import shutil
import subprocess
import json
import tempfile

from resqui.core import CheckResult
from resqui.tools import normalized, construct_full_url
from resqui.executors import DockerExecutor, PythonExecutor


class IndicatorPlugin:
    """Skeleton for an Indicator Plugin"""

    name = None
    version = None
    id = None
    indicators = []


class HowFairIs(IndicatorPlugin):
    name = "HowFairIs"
    version = "0.14.2"
    python_package_name = "howfairis"
    id = "https://w3id.org/everse/tools/howfairis"
    indicators = ["has_license"]

    def __init__(self, context):
        self.context = context
        self.executor = PythonExecutor()
        self.executor.install(f"{self.python_package_name}=={self.version}")

    def has_license(self, url, branch_hash_or_tag):
        script = normalized(
            f"""
            from howfairis import Repo, Checker
            repo = Repo("{url}", "{branch_hash_or_tag}")
            checker = Checker(repo, is_quiet=True)
            print(checker.has_license())
        """
        )
        result = self.executor.execute(script)
        output = "valid" if result.stdout.strip() == "True" else "invalid"
        if output == "valid":
            evidence = "Found license file: 'LICENSE'."
            success = True
        else:
            evidence = "No license file found."
            success = False

        return CheckResult(
            process="Searches for a file named 'LICENSE' or 'LICENSE.md' in the repository root.",  # noqa: E501
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )


class CFFConvert(IndicatorPlugin):
    name = "CFFConvert"
    version = "2.0.0"
    python_package_name = "cffconvert"
    id = "https://w3id.org/everse/tools/cffconvert"
    indicators = ["has_citation"]

    def __init__(self, context):
        self.context = context
        self.executor = PythonExecutor()
        self.executor.install(f"{self.python_package_name}=={self.version}")

    def has_citation(self, url, branch_hash_or_tag):
        full_url = construct_full_url(url, branch_hash_or_tag)
        script = normalized(
            f"""
            from cffconvert.cli.create_citation import create_citation
            citation = create_citation(None, "{full_url}")
            if citation.validate() is None:
                print("True")
        """
        )
        result = self.executor.execute(script)

        output = "valid" if result.stdout.strip() == "True" else "invalid"
        if output == "valid":
            evidence = "Found valid CITATION.cff file in repository root."
            success = True
        else:
            evidence = "No valid CITATION.cff file found in repository root."
            success = False

        return CheckResult(
            process="Searches for a 'CITATION.cff' file in the repository root and validates its syntax.",  # noqa: E501
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )


class Gitleaks(IndicatorPlugin):
    name = "GitLeaks"
    version = "8.24.2"
    image_url = f"ghcr.io/gitleaks/gitleaks:v{version}"
    id = "https://w3id.org/everse/tools/gitleaks"
    indicators = ["has_no_security_leak"]

    def __init__(self, context):
        self.context = context
        self.executor = DockerExecutor(self.image_url)

    def has_no_security_leak(self, url, branch_hash_or_tag):
        temp_dir = tempfile.mkdtemp()
        report_fname = "report.json"

        try:
            subprocess.run(
                ["git", "clone", url, temp_dir],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error cloning {url}: {e}")
            raise

        run_args = ["-v", f"{temp_dir}:/path"]
        p = self.executor.run(
            ["git", "/path", "-r", f"/path/{report_fname}"], run_args=run_args
        )
        with open(os.path.join(temp_dir, report_fname)) as f:
            report = json.load(f)

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        if "no leaks found" in p.stderr and not report:
            output = "secure"
            evidence = "No leaks have been found."
            success = True
        else:
            output = "insecure"
            evidence = "Leaks have been found."
            success = False

        return CheckResult(
            process="Searches for security leaks in the full repository history.",  # noqa: E501
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )


class SuperLinter(IndicatorPlugin):
    name = "SuperLinter"
    version = "7.3.0"
    image_url = f"ghcr.io/super-linter/super-linter:v{version}"
    id = "https://w3id.org/everse/tools/superlinter"
    indicators = ["has_no_linting_issues"]

    def __init__(self, context):
        self.context = context
        machine = platform.machine()
        pull_args = ["--platform", "linux/amd64"] if machine == "arm64" else []
        self.executor = DockerExecutor(self.image_url, pull_args=pull_args)

    def has_no_linting_issues(self, url, branch):
        temp_dir = tempfile.mkdtemp()

        try:
            subprocess.run(
                ["git", "clone", url, temp_dir],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error cloning {url}: {e}")
            raise

        run_args = [
            #            "-e",
            #            "LOG_LEVEL=DEBUG",
            "-e",
            "RUN_LOCAL=true",
            "-e",
            f"DEFAULT_BRANCH={branch}",
            "-v",
            f"{temp_dir}:/tmp/lint",
        ]
        p = self.executor.run([], run_args=run_args)

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        if "Super-linter detected linting errors" in p.stdout:
            output = "invalid"
            evidence = "Linting errors have been detected."
            success = False
        else:
            output = "valid"
            evidence = "No linting errors have been detected."
            success = True

        # print("STDOUT")
        # print(p.stdout)
        # print()
        # print("STDERR")
        # print(p.stderr)

        return CheckResult(
            process="Searches for linting errors.",  # noqa: E501
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )


class OpenSSFScorecard:
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

    def execute(self, url):
        if url in self._cache:
            return self._cache[url]

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
                self._cache[url] = out
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

    def has_ci_tests(self, url, branch):
        results = self.execute(url)
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
            process="Calculates the CI-Tests score.",  # noqa: E501
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )

    def human_code_review_requirement(self, url, branch):
        results = self.execute(url)
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
            process="Calculates the Code-Review score.",  # noqa: E501
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )

    def has_published_package(self, url, branch):
        results = self.execute(url)
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
            process="Calculates the Packaging score.",  # noqa: E501
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )
