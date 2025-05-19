class ProvidersList(list):
    def __init__(self, *items):
        super().__init__(items)

    def __getitem__(self, key):
        if isinstance(key, str):
            if key == '':
                return self
            return [item for item in self if item.__class__.__name__.lower() == key][0]
        return super().__getitem__(key)
