"""
Usage:
    resqui -c <config_file> <repository_url>

Options:
    <repository_url>  URL of the repository to be analyzed.
    -c <config_file>  Path to the configuration file.
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
    def __init__(self, filepath):
        with open(filepath) as f:
            self._cfg = json.load(f)


class Spinner:
    """
    A simple spinner class to indicate progress in the console.
    Use it as a context manager.
    """

    def __init__(self):
        self.spinning = False
        self.spinner_thread = None

    def start(self):
        self.spinning = True
        self.spinner_thread = threading.Thread(target=self._spinner)
        self.spinner_thread.start()

    def stop(self):
        self.spinning = False
        if self.spinner_thread:
            self.spinner_thread.join()

    def _spinner(self):
        for char in itertools.cycle("|/-\\"):
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(0.1)
            sys.stdout.write("\b")
            if not self.spinning:
                break

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()


def resqui():
    args = docopt(__doc__, version=__version__)

    configuration = Configuration(args["-c"])
    url = args["<repository_url>"]

    for indicator in configuration._cfg["indicators"]:
        print(
            f"  Checking indicator {indicator['name']}/{indicator['plugin']}:",
            end=" ",
        )
        sys.stdout.flush()

        with Spinner():
            base_package = __name__.rsplit(".", 1)[0]
            plugin_class = indicator["plugin"]
            plugin_module = importlib.import_module(base_package + ".plugins")
            plugin_instance = getattr(plugin_module, plugin_class)()
            plugin_method = indicator["name"]
            result = getattr(plugin_instance, plugin_method)(url)

        if result:
            print("\033[92mTrue\033[0m")
        else:
            print("\033[91mFalse\033[0m")
