"""
Usage:
    resqui -c <config_file>
    resqui [--version] [--help]

Options:
    -c <config_file>  Path to the configuration file.
    --version         Show the version of the script.
    --help            Show this help message."
"""
from .docopt import docopt
from .version import __version__


class Configuration:
    pass


def resqui():
    args = docopt(__doc__, version=__version__)
    print(args)

    # configuration = Configuration()
    # pipeline = configuration.get_pipeline(args['-c'])
