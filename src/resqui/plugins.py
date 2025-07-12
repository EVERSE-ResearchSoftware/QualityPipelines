import os
import venv
import platform
import shutil
import subprocess
import tempfile
import json

from .core import CheckResult


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


class IndicatorPlugin:
    """Skeleton for an Indicator Plugin"""

    name = None
    version = None
    id = None
    indicators = []


class PythonExecutor:
    """A Python executor which uses a temporary virtual environment.

    The `packages` should be a list of package names with optional
    requirement specifiers as accepted by `pip`.

    More information:
    https://packaging.python.org/en/latest/glossary/#term-Requirement-Specifier

    """

    def __init__(self, packages=None):
        """Instantiates a virtual environment in a temporary folder."""
        self.temp_dir = tempfile.mkdtemp()
        venv.create(self.temp_dir, with_pip=True)
        if packages is None:
            return
        for package in packages:
            self.install(package)

    def install(self, package):
        try:
            subprocess.run(
                [f"{self.temp_dir}/bin/pip", "install", package],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error installing {package} with pip: {e}")
            raise

    def is_installed(self, package_name, version=None):
        out = self.execute(
            normalized(
                """
            from importlib.metadata import distributions
            for dist in distributions():
                name = dist.metadata.get('Name', '<unknown>')
                version = getattr(dist, 'version', '<unknown>')
                print(f"{name}=={version}")
        """
            )
        )
        package = package_name + "" if version is None else f"=={version}"
        return package in out.stdout

    def execute(self, script):
        """Run the script in the virtual environment."""
        return subprocess.run(
            [f"{self.temp_dir}/bin/python", "-c", script],
            capture_output=True,
            text=True,
        )

    def __del__(self):
        """Cleanup the temporary virtual environment on destruction."""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Failed to remove virtualenv at {self.temp_dir}: {e}")


class DockerExecutor:
    """A Docker executor."""

    def __init__(self, image_url, pull_args=None):
        self.url = image_url
        if pull_args is None:
            pull_args = []
        try:
            subprocess.run(
                ["docker", "pull"] + pull_args + [self.url],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error pulling the Docker image from {self.url}: {e}")
            raise

    def run(self, command, run_args=None):
        """
        Run command (popenargs) inside a Docker container and return a
        CompletedProcess instance from the subprocess Python module.

        Extra arguments to the command can be passed as a list of
        strings via `run_args`.
        """
        if run_args is None:
            run_args = []
        cmd = ["docker", "run"] + run_args + [self.url] + command
        return subprocess.run(cmd, capture_output=True, text=True)


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

    def has_license(self, url, branch):
        script = normalized(
            f"""
            from howfairis import Repo, Checker
            repo = Repo("{url}", "{branch}")
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

    def has_citation(self, url, branch):
        script = normalized(
            f"""
            from cffconvert.cli.create_citation import create_citation
            citation = create_citation(None, "{url}")
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

    def has_no_security_leak(self, url, branch):
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

        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Failed to remove clone repository at {temp_dir}: {e}")

        if "no leaks found" in p.stderr and not report:
            return True
        return False


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

        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Failed to remove clone repository at {temp_dir}: {e}")

        if "Super-linter detected linting errors" in p.stdout:
            return False
        # print("STDOUT")
        # print(p.stdout)
        # print()
        # print("STDERR")
        # print(p.stderr)

        return True


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
        return self.get_score(results, "CI-Tests") >= 5

    def human_code_review_requirement(self, url, branch):
        results = self.execute(url)
        return self.get_score(results, "Code-Review") >= 5

    def has_published_package(self, url, branch):
        results = self.execute(url)
        return self.get_score(results, "Packaging") >= 5
