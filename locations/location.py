class Location:
    next_key: int = 0

    def __init__(self, name: str) -> None:
        self.name = name
        self.key = Location.next_key
        Location.next_key += 1

    def __str__(self) -> str:
        return self.name
