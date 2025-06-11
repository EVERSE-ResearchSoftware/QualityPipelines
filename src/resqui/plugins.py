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


class IndicatorPlugin:
    pass


class PythonExecutor:
    """A Python executor which uses a temporary virtual environment."""

    required_members = ["python_package_name", "version"]
    python_package_name = None
    version = None

    def instantiate(self):
        """Instantiates a virtual environment in a temporary folder."""
        if self.python_package_name is None:
            print(
                f"The Python executor of the Plugin {self.name} "
                f"v{self.version} does not specify a Python package "
                "name ('python_package_name')"
            )
            exit(1)
        self.temp_dir = tempfile.mkdtemp()
        venv.create(self.temp_dir, with_pip=True)
        try:
            subprocess.run(
                [
                    f"{self.temp_dir}/bin/pip",
                    "install",
                    f"{self.python_package_name}=={self.version}",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error installing {self.name} v{self.version}: {e}")
            raise

    def execute(self, script):
        """Run the script in the virtual environment."""
        return subprocess.run(
            [f"{self.temp_dir}/bin/python", "-c", script],
            capture_output=True,
            text=True,
        )


class HowFairIs(IndicatorPlugin, PythonExecutor):
    name = "HowFairIs"
    version = "0.14.2"
    python_package_name = "howfairis"
    id = "https://w3id.org/everse/tools/howfairis"
    indicators = ["has_license"]

    def __init__(self):
        self.instantiate()

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
        machine = platform.machine()
        cmd = (
            ["docker", "pull"]
            + (["--platform", "linux/amd64"] if machine == "arm64" else [])
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
