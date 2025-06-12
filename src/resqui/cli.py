"""
Usage:
    resqui [options] -c <config_file> <repository_url>
    resqui indicators

Options:
    <repository_url>   URL of the repository to be analyzed.
    -c <config_file>   Path to the configuration file.
    -o <output_file>   Path to the output file [default: resqui_summary.json].
    -t <github_token>  GitHub API token.
    -b <branch>        The Git branch to be checked [default: main].
    --version          Show the version of the script.
    --help             Show this help message.
"""

import itertools
import time
import threading
import importlib
import sys

from .core import Configuration, Context, Summary
from .plugins import IndicatorPlugin
from .api import Publisher
from .docopt import docopt
from .version import __version__


class Spinner:
    """
    A simple spinner class to indicate progress in the console.
    Use it as a context manager.
    """

    def __init__(self):
        self.spinning = False
        self.spinner_thread = None
        self.start_time = time.time()

    def start(self):
        self.spinning = True
        self.spinner_thread = threading.Thread(target=self._spinner)
        self.spinner_thread.start()

    def stop(self):
        self.spinning = False
        elapsed_time = time.time() - self.start_time
        if self.spinner_thread:
            self.spinner_thread.join()
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


def resqui():
    args = docopt(__doc__, version=__version__)

    if args["indicators"]:
        print_indicator_plugins()
        exit(0)

    configuration = Configuration(args["-c"])
    output_file = args["-o"]
    url = args["<repository_url>"]
    branch = args["-b"]
    github_token = args["-t"]

    if github_token is not None:
        print("GitHub API token \033[92m✔\033[0m")

    context = Context(github_token=github_token)

    print(f"Repository URL: {url}")
    print(f"Branch: {branch}")
    print("Checking indicators ...")

    publisher = Publisher()
    summary = Summary()
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
            result = getattr(plugin_instance, plugin_method)(url, branch)

        if result:
            print("\033[92m✔\033[0m")
        else:
            print("\033[91m✖\033[0m")

        status = "success" if result else "fail"

        summary.add_indicator_result(indicator, plugin_class, status)

    summary.to_json(output_file)
    print(f"Summary has been written to {output_file}")

    print("Publishing summary ", end=" ")
    sys.stdout.flush()
    success = publisher.upload(summary)
    if success:
        print("\033[92m✔\033[0m")
    else:
        print("\033[91m✖\033[0m")


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
