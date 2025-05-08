class ProvidersList(list):
    def __getitem__(self, key):
        if isinstance(key, str):
            return [item for item in self if item.__class__.__name__.lower() == key]
        return super().__getitem__(key)
