import os
import venv
import platform
import subprocess
import tempfile
import json


def normalized(script):
    """
    Removes extra indentation from a script, caused by triple quotes.
    This does not support mixed tab/spaces.
    """
    lines = script.splitlines()
    lines = [line for line in lines if line.strip()]  # remove empty lines
    first_line = lines[0]
    leading_whitespace = len(first_line) - len(first_line.lstrip())
    return "\n".join(line[leading_whitespace:] for line in lines)


class HowFairIs:
    name = "HowFairIs"
    version = "0.14.2"
    id = "https://w3id.org/everse/tools/howfairis"
    indicators = ["has_license"]

    def __init__(self):
        self.instantiate()

    def instantiate(self):
        self.temp_dir = tempfile.mkdtemp()
        venv.create(self.temp_dir, with_pip=True)
        try:
            subprocess.run(
                [
                    f"{self.temp_dir}/bin/pip",
                    "install",
                    f"howfairis=={self.version}",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error installing howfairis: {e}")
            raise

    def has_license(self, url, branch):
        script = normalized(
            f"""
            from howfairis import Repo, Checker
            repo = Repo("{url}", "{branch}")
            checker = Checker(repo, is_quiet=True)
            print(checker.has_license())
        """
        )
        result = self.execute(script)
        return result.stdout.strip() == "True"

    def execute(self, script):
        return subprocess.run(
            [f"{self.temp_dir}/bin/python", "-c", script],
            capture_output=True,
            text=True,
        )


class CFFConvert:
    name = "CFFConvert"
    version = "2.0.0"
    id = "https://w3id.org/everse/tools/cffconvert"
    indicators = ["has_citation"]

    def __init__(self):
        self.instantiate()

    def instantiate(self):
        self.temp_dir = tempfile.mkdtemp()
        venv.create(self.temp_dir, with_pip=True)
        try:
            subprocess.run(
                [
                    f"{self.temp_dir}/bin/pip",
                    "install",
                    f"cffconvert=={self.version}",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error installing cffconvert: {e}")
            raise

    def has_citation(self, url, branch):
        script = normalized(
            f"""
            from cffconvert.cli.create_citation import create_citation
            citation = create_citation(None, "{url}")
            if citation.validate() is None:
                print("True")
        """
        )
        result = self.execute(script)
        return result.stdout.strip() == "True"

    def execute(self, script):
        return subprocess.run(
            [f"{self.temp_dir}/bin/python", "-c", script],
            capture_output=True,
            text=True,
        )


class Gitleaks:
    name = "GitLeaks"
    version = "8.24.2"
    id = "https://w3id.org/everse/tools/gitleaks"
    indicators = ["has_security_leak"]

    def __init__(self):
        self.instantiate()

    def instantiate(self):
        try:
            subprocess.run(
                [
                    "docker",
                    "pull",
                    f"ghcr.io/gitleaks/gitleaks:v{self.version}",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error pulling the Gitleaks Docker image: {e}")
            raise

    def has_security_leak(self, url, branch):
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

        cmd = [
            "docker",
            "run",
            "-v",
            f"{temp_dir}:/path",
            f"ghcr.io/gitleaks/gitleaks:v{self.version}",
            "git",
            "/path",
            "-r",
            f"/path/{report_fname}",
        ]
        p = subprocess.run(cmd, capture_output=True, text=True)
        with open(os.path.join(temp_dir, report_fname)) as f:
            report = json.load(f)

        if "no leaks found" in p.stderr and not report:
            return True
        return False


class SuperLinter:
    name = "SuperLinter"
    version = "7.3.0"
    id = "https://w3id.org/everse/tools/superlinter"
    indicators = ["has_no_linting_issues"]

    def __init__(self):
        self.instantiate()

    def instantiate(self):
        cmd = (
            ["docker", "pull"]
            + (
                ["--platform", "linux/amd64"]
                if platform.machine() == "arm64"
                else []
            )
            + [f"ghcr.io/super-linter/super-linter:v{self.version}"]
        )

        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error pulling the Super-Linter Docker image: {e}")
            raise

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

        cmd = [
            "docker",
            "run",
            "-e",
            "LOG_LEVEL=DEBUG",
            "-e",
            "RUN_LOCAL=true",
            "-e",
            f"DEFAULT_BRANCH={branch}",
            "-v",
            f"{temp_dir}:/tmp/lint",
            f"ghcr.io/super-linter/super-linter:v{self.version}",
        ]
        subprocess.run(cmd, capture_output=True, text=True)

        # print("STDOUT")
        # print(p.stdout)
        # print()
        # print("STDERR")
        # print(p.stderr)

        return False


class OpenSSFScorecard:
    name = "OpenSSF Scorecard"
    id = "https://github.com/ossf/scorecard"
    version = "v5.1.1"
    indicators = [
        "has_ci_tests",
        "human_code_review_requirement",
        "has_published_package"
    ]

    def __init__(self):
        self.instantiate()

    def instantiate(self):
        try:
            subprocess.run(
                ["docker", "pull", f"gcr.io/openssf/scorecard:{self.version}"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError as e:
            print(f"Error pulling OpenSSF Scorecard image: {e}")
            raise

    def execute(self, url):
        cmd = [
            "docker", "run", "--rm",
            "-e", f"GITHUB_AUTH_TOKEN={github_token}",
            f"gcr.io/openssf/scorecard:{self.version}",
            "--repo", url,
            "--format", "json"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if result.stdout:
                return json.loads(result.stdout)
            else:
                raise ValueError("No output received from Scorecard.")
        except subprocess.CalledProcessError as e:
            print("Scorecard error output:")
            print(e.stderr)
            raise
        except json.JSONDecodeError:
            print("JSON output not valid:")
            print(result.stdout)
            raise

    def get_score(self, results, check_name):
        checks = results["checks"]
        if not checks:
            raise ValueError("No checks found in results.")
        check = results[check_name]
        if check is not None:
            return check["score"]
        return 0

    def has_ci_tests(self, url, branch):
        results = self.execute(url)
        return self.get_score(results, "CI-Tests") >= 5

    def human_code_review_requirement(self, url, branch):
        results = self.execute(url)
        return self.get_score(results, "Code-Review") >= 5

    def has_published_package(self, url, branch):
        results = self.execute(url)
        return self.get_score(results, "Packaging") >= 5