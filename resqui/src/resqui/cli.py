"""
Usage:
    resqui -c <config_file> <repository_url>

Options:
    <repository_url>  URL of the repository to be analyzed.
    -c <config_file>  Path to the configuration file.
    --version         Show the version of the script.
    --help            Show this help message.
"""
import importlib
import json
from .docopt import docopt
from .version import __version__


class Configuration:
    def __init__(self, filepath):
        with open(filepath) as f:
            self._cfg = json.load(f)


def resqui():
    args = docopt(__doc__, version=__version__)

    configuration = Configuration(args["-c"])
    url = args["<repository_url>"]

    for indicator in configuration._cfg["indicators"]:
        base_package = __name__.rsplit(".", 1)[0]
        plugin_class = indicator["plugin"]
        plugin_module = importlib.import_module(base_package + ".plugins")
        plugin_instance = getattr(plugin_module, plugin_class)()
        plugin_method = indicator["name"]
        result = getattr(plugin_instance, plugin_method)(url)
        print(f"  {indicator['name']}: {result}")
