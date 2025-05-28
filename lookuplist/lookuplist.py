"""
    Lookup list class
"""
from collections.abc import Sequence
from typing import overload, Union, TypeVar

T = TypeVar("T")

class LookupList(Sequence[T]):
    """
    List extension, allowing indexing by class name of the list item

    Example usage:
        lst = LookupList(Class1(), Class1(), Class2())
        lst['class1'] # -> same as lst[0]
        lst[''] # -> same as lst
    """

    def __init__(self, *items: T) -> None:
        """Initialize LookupList with optional fallback items."""
        self._items = list(items)

    @overload
    def __getitem__(self, key: int) -> T:
        ...

    @overload
    def __getitem__(self, key: slice) -> list[T]:
        ...

    @overload
    def __getitem__(self, key: str) -> Union[T, 'LookupList']:
        ...

    def __getitem__(self, key: object) -> Union[T, list[T], 'LookupList[T]']:
        """
            Return item by key or fallback logic if key not found.
        """
        if isinstance(key, str):
            if key == '' or key == '*':
                return self
            try:
                return next(item for item in self._items if item.__class__.__name__.lower() == key.lower())
            except StopIteration:
                raise KeyError(f"No item with class name '{key}' found.")
        if isinstance(key, (int, slice)):
            return self._items[key]
        raise TypeError(f"Invalid key type: {type(key)}")

    def __contains__(self, key: object) -> bool:
        """
            Check if the key exists either directly or through fallback.
        """
        if isinstance(key, str):
            return any(item.__class__.__name__.lower() == key.lower() for item in self._items)
        return key in self._items

    def __repr__(self) -> str:
        """
            Return string representation of the LookupList.
        """
        return f"<LookupList[{', '.join(item.__class__.__name__ for item in self._items)}]>"

    def __len__(self) -> int:
        return len(self._items)