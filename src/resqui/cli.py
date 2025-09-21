"""
Usage:
    resqui [options]
    resqui indicators

Options:
    -u <repository_url>  URL of the repository to be analyzed.
    -c <config_file>     Path to the configuration file.
    -o <output_file>     Path to the output file [default: resqui_summary.json].
    -t <github_token>    GitHub API token.
    -b <branch>          The Git branch to be checked.
    --version            Show the version of the script.
    --help               Show this help message.
"""

import itertools
import time
import threading
import importlib
import os
import shutil
import subprocess
import sys
import tempfile

from resqui.core import Context, Summary
from resqui.config import Configuration
from resqui.tools import to_https, project_name_from_url
from resqui.plugins import IndicatorPlugin
from resqui.docopt import docopt
from resqui.version import __version__


class Spinner:
    """
    A simple spinner class to indicate progress in the console.
    Use it as a context manager.
    """

    def __init__(self, print_time=True):
        self.spinning = False
        self.spinner_thread = None
        self.start_time = time.time()
        self.print_time = print_time

    def start(self):
        self.spinning = True
        self.spinner_thread = threading.Thread(target=self._spinner)
        self.spinner_thread.start()

    def stop(self):
        self.spinning = False
        elapsed_time = time.time() - self.start_time
        if self.spinner_thread:
            self.spinner_thread.join()
        if self.print_time:
            print(f"({elapsed_time:.1f}s)", end=": ")

    def _spinner(self):
        for char in itertools.cycle("|/-\\"):
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(0.1)
            sys.stdout.write("\b")
            if not self.spinning:
                break

    def __enter__(self):
        if not sys.stdout.isatty():
            return self
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()


class GitInspector:
    def __init__(self, path="."):
        self.path = os.path.abspath(path)

    def git(self, *args):
        return subprocess.check_output(
            ["git", "-C", self.path] + list(args), text=True
        ).strip()

    @property
    def version(self):
        return self.git("describe", "--tags", "--always")

    @property
    def project_name_from_url(self):
        return project_name_from_url(self.remote_url)

    @property
    def current_commit_hash(self):
        return self.git("rev-parse", "HEAD")

    @property
    def author(self):
        return self.git("show", "-s", "--pretty=format:%an", "HEAD")

    @property
    def email(self):
        return self.git("show", "-s", "--pretty=format:%ae", "HEAD")

    @property
    def remote_url(self):
        return self.git("config", "--get", "remote.origin.url")

    @property
    def remote_https_url(self):
        return to_https(self.remote_url)


def resqui():
    args = docopt(__doc__, version=__version__)

    if args["indicators"]:
        print_indicator_plugins()
        exit(0)

    configuration = Configuration(args["-c"])
    output_file = args["-o"]
    url = args["-u"]
    branch = args["-b"]
    github_token = args["-t"]

    temp_dir = None
    if url is None:
        gitinspector = GitInspector()
    else:
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
        gitinspector = GitInspector(temp_dir)

    url = gitinspector.remote_https_url
    project_name = gitinspector.project_name_from_url
    author = gitinspector.author
    email = gitinspector.email
    software_version = gitinspector.version

    if temp_dir is not None:
        shutil.rmtree(temp_dir)

    if branch is None:
        gitinspector = GitInspector()
        branch_hash_or_tag = gitinspector.current_commit_hash

    if github_token is not None:
        print("GitHub API token \033[92m✔\033[0m")
    else:
        print("GitHub API token \033[91m✖\033[0m")

    context = Context(github_token=github_token)

    print(f"Repository URL: {url}")
    print(f"Project name: {project_name}")
    print(f"Author: {author}")
    print(f"Email: {email}")
    print(f"Version: {software_version}")
    print(f"Branch, tag or commit hash: {branch_hash_or_tag}")
    print("Checking indicators ...")

    summary = Summary(
        author, email, project_name, url, software_version, branch_hash_or_tag
    )
    plugin_instances = {}
    for indicator in configuration._cfg["indicators"]:
        print(
            f"    {indicator['name']}/{indicator['plugin']}",
            end=" ",
        )
        sys.stdout.flush()

        base_package = __name__.rsplit(".", 1)[0]
        plugin_class_name = indicator["plugin"]

        if plugin_class_name not in plugin_instances:
            plugin_module = importlib.import_module(base_package + ".plugins")
            plugin_class = getattr(plugin_module, plugin_class_name)
            with Spinner(print_time=False):
                plugin_instances[plugin_class_name] = plugin_class(context)

        plugin_instance = plugin_instances[plugin_class_name]
        plugin_method = indicator["name"]

        with Spinner():
            result = getattr(plugin_instance, plugin_method)(url, branch_hash_or_tag)

        if result:
            print("\033[92m✔\033[0m")
        else:
            print("\033[91m✖\033[0m")

        summary.add_indicator_result(indicator, plugin_class, result)

    summary.write(output_file)
    print(f"Summary has been written to {output_file}")

    print("Publishing summary ", end=" ")
    sys.stdout.flush()
    try:
        summary.upload()
    except (RuntimeError, ValueError) as e:
        print(f"\033[91m✖\033[0m {e}")
    else:
        print("\033[92m✔\033[0m")


def print_indicator_plugins():
    """
    Prints a list of available indicator plugins.
    """

    def subclasses(cls):
        return set(cls.__subclasses__()).union(
            s for c in cls.__subclasses__() for s in subclasses(c)
        )

    for cls in sorted(subclasses(IndicatorPlugin), key=lambda c: c.__name__):
        print(f"Class: {cls.__name__}")
        for attr in ["name", "version", "id"]:
            value = getattr(cls, attr, None)
            print(f"  {attr.capitalize()}: {value}")
        indicators = getattr(cls, "indicators", [])
        print("  Indicators:")
        if indicators:
            for ind in indicators:
                print(f"    - {ind}")
        else:
            print("    (none)")
        print()
