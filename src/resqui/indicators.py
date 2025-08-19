class Indicator:
    _subclasses = []

    @classmethod
    def register_subclass(cls, subclass):
        cls._subclasses.append(subclass)

    @classmethod
    def get_subclasses(cls):
        return cls._subclasses
