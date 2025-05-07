"""
Usage:
    resqui [options] -c <config_file> <repository_url>

Options:
    <repository_url>  URL of the repository to be analyzed.
    -c <config_file>  Path to the configuration file.
    -o <output_file>  Path to the output file [default: resqui_summary.json].
    -b <branch>       The Git branch to be checked [default: main].
    --version         Show the version of the script.
    --help            Show this help message.
"""
import itertools
import time
import threading
import importlib
import json
import sys
from .docopt import docopt
from .version import __version__


class Configuration:
    """
    A basic wrapper for the configuration.
    """

    def __init__(self, filepath):
        with open(filepath) as f:
            self._cfg = json.load(f)


class Summary:
    """
    Summary of the results of the checks.
    """

    def __init__(self):
        self.checks = []

    def add_indicator_result(self, indicator, checking_software, status):
        self.checks.append(
            {
                "checking_software": {
                    "name": checking_software.name,
                    "id": checking_software.id,
                    "version": checking_software.version,
                },
                "indicator": indicator,
                "status": status,
            }
        )

    def to_json(self, filename):
        with open(filename, "w") as f:
            json.dump(self.checks, f, indent=4)


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

    configuration = Configuration(args["-c"])
    output_file = args["-o"]
    url = args["<repository_url>"]
    branch = args["-b"]

    print("Checking indicators...")

    summary = Summary()
    for indicator in configuration._cfg["indicators"]:
        print(
            f"    {indicator['name']}/{indicator['plugin']}",
            end=" ",
        )
        sys.stdout.flush()

        base_package = __name__.rsplit(".", 1)[0]
        plugin_class_name = indicator["plugin"]
        plugin_module = importlib.import_module(base_package + ".plugins")
        plugin_class = getattr(plugin_module, plugin_class_name)
        plugin_method = indicator["name"]
        with Spinner():
            plugin_instance = plugin_class()
            result = getattr(plugin_instance, plugin_method)(url, branch)

        if result:
            print("\033[92m✔\033[0m")
        else:
            print("\033[91m✖\033[0m")

        status = "success" if result else "fail"

        summary.add_indicator_result(indicator, plugin_class, status)

    summary.to_json(output_file)
    print(f"Summary has been written to {output_file}")
