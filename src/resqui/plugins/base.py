class PluginInitError(Exception):
    """Thrown if the initialisation of a plugin fails (e.g. missing GITHUB token)"""

    pass


class IndicatorPlugin:
    """Skeleton for an Indicator Plugin"""

    name = None
    version = None
    id = None
    indicators = []
