"""
Usage:
    resqui [options]
    resqui indicators

Options:
    -u <repository_url>   URL of the repository to be analyzed (GitHub URLs, Zenodo DOIs and URLs accepted).
    -p <project_path>     Path to a local project directory to be analyzed without requiring Git history.
    -c <config_file>      Path to the configuration file.
    -o <output_file>      Path to the output file [default: resqui_summary.json].
    -t <github_token>     GitHub API token.
    -d <dashverse_token>  DashVerse API token.
    -b <branch>           The Git branch to be checked.
    -v                    Verbose output.
    --version             Show the version of the script.
    --help                Show this help message.
"""

import importlib
import itertools
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

from resqui.config import Configuration
from resqui.core import Context, Summary
from resqui.docopt import docopt
from resqui.executors import ExecutorInitError
from resqui.plugins import IndicatorPlugin, PluginInitError
from resqui.tools import (
    ensure_list,
    indented,
    is_zenodo_url,
    project_name_from_url,
    to_https,
    zenodo_url_to_git,
)
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

    @property
    def is_a_git_repository(self):
        return os.path.isdir(os.path.join(self.path, ".git"))


def resqui():
    args = docopt(__doc__, version=__version__)

    if args["indicators"]:
        print_indicator_plugins()
        exit(0)

    configuration = Configuration(args["-c"])
    output_file = args["-o"]
    url = args["-u"]
    project_path = args["-p"]
    branch = args["-b"]
    github_token = args["-t"]
    dashverse_token = args["-d"]
    verbose = args["-v"]

    temp_dir = None
    local_path = None
    if project_path is not None:
        if url is not None:
            print("Error: -u and -p are mutually exclusive.")
            exit(1)
        local_path = os.path.abspath(os.path.expanduser(os.path.expandvars(project_path)))
        if not os.path.isdir(local_path):
            print(
                f"Error: Project path does not exist or is not a directory: {local_path}"
            )
            exit(1)
        url = local_path
        project_name = os.path.basename(local_path.rstrip(os.sep)) or local_path
        author = "local"
        email = "local"
        software_version = "local"
        branch_hash_or_tag = branch if branch is not None else "local"
    elif url is None:
        gitinspector = GitInspector()
        if not gitinspector.is_a_git_repository:
            print(
                "Error: Not a Git repository. Either run resqui from within a repository or specify one with -u <url>"
            )
            exit(1)

        url = gitinspector.remote_https_url
        project_name = gitinspector.project_name_from_url
        author = gitinspector.author
        email = gitinspector.email
        software_version = gitinspector.version
        branch_hash_or_tag = (
            gitinspector.current_commit_hash if branch is None else branch
        )
    else:
        if is_zenodo_url(url):
            url, branch = zenodo_url_to_git(url)

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
        branch_hash_or_tag = (
            gitinspector.current_commit_hash if branch is None else branch
        )

    if temp_dir is not None:
        shutil.rmtree(temp_dir)

    if github_token is not None:
        print("GitHub API token \033[92m✔\033[0m")
    else:
        print("GitHub API token \033[91m✖\033[0m")

    context = Context(
        github_token=github_token,
        dashverse_token=dashverse_token,
        local_path=local_path,
    )

    if local_path is not None:
        print(f"Project path: {local_path}")
    else:
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
            f"  {indicator['name']}/{indicator['plugin']}",
            end=" ",
        )
        sys.stdout.flush()

        base_package = __name__.rsplit(".", 1)[0]
        plugin_class_name = indicator["plugin"]

        if plugin_class_name not in plugin_instances:
            plugin_module = importlib.import_module(base_package + ".plugins")
            plugin_class = getattr(plugin_module, plugin_class_name)
            if context.local_path is not None and not getattr(
                plugin_class, "supports_local_path", False
            ):
                print(
                    f"⚠️  {plugin_class_name} does not support local project path mode (skipping its indicators)"
                )
                continue
            with Spinner(print_time=False):
                try:
                    plugin_instances[plugin_class_name] = plugin_class(context)
                except (ExecutorInitError, PluginInitError) as e:
                    print(f"⚠️  {e} (skipping its indicators)")
                    continue

        plugin_instance = plugin_instances[plugin_class_name]
        plugin_method = indicator["name"]

        with Spinner():
            results = getattr(plugin_instance, plugin_method)(url, branch_hash_or_tag)

        for result in ensure_list(results):
            status = "\033[92m✔\033[0m" if result else "\033[91m✖\033[0m"
            if verbose:
                print(indented("\n" + result.evidence + status, 4), end="")
            else:
                print(status, end=" ")

            summary.add_indicator_result(indicator, plugin_class, result)
        print()

    summary.write(output_file)
    print(f"Summary has been written to {output_file}")

    print("Publishing summary ", end="")
    sys.stdout.flush()
    try:
        summary.upload(context.dashverse_token)
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
