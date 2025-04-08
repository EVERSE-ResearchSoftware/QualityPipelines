import os
import venv
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
    indicators = ["has_license"]
    version = "0.14.2"

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

    def has_license(self, url):
        script = normalized(
            f"""
            from howfairis import Repo, Checker
            url = "{url}"
            repo = Repo(url)
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
    indicators = ["has_citation"]
    version = "2.0.0"

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

    def has_citation(self, url):
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
    indicators = ["has_security_leak"]
    version = "8.24.2"

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

    def has_security_leak(self, url):
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
        subprocess.run(cmd, capture_output=True, text=True)
        with open(os.path.join(temp_dir, report_fname)) as f:
            report = json.load(f)

        if report:
            return True
        return False
