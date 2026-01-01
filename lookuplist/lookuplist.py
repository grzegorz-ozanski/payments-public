"""
    Lookup list class
"""
from collections.abc import Sequence
from typing import overload, Union, TypeVar

T = TypeVar('T')

class LookupList(Sequence[T]):
    """
    List extension, allowing indexing by class name of the list item

    Example usage:
        lst = LookupList(Class1(), Class1(), Class2())
        lst['class1'] # -> same as lst[0]
        lst[''] # -> same as lst
    """

    def __init__(self, *items: T) -> None:
        """Initialize the LookupList with optional fallback items."""
        self._items = list(items)

    @overload
    def __getitem__(self, key: int) -> T:
        ...

    @overload
    def __getitem__(self, key: slice) -> list[T]:
        ...

    @overload
    def __getitem__(self, key: str) -> Union[T, 'LookupList[T]']:
        ...

    @overload
    def __getitem__(self, key: tuple[str,...]) -> Union[T, 'LookupList[T]']:
        ...

    def __getitem__(self, key: object) -> Union[T, list[T], 'LookupList[T]']:
        """
            Return an item by key or fallback logic if key not found.
        """
        if isinstance(key, tuple):
            result = []
            for item in key:
                result.append(self[item])
            return result
        if isinstance(key, str):
            if key == '' or key == '*':
                return self
            return self.__find__(key)
        if isinstance(key, (int, slice)):
            if isinstance(key, slice) and (isinstance(key.start, str) or isinstance(key.stop, str)):
                parts = [key.start, key.stop]
                slice_parts = [-1, -1]
                for index, value in enumerate(parts):
                    slice_parts[index] = self._items.index(self.__find__(value)) if isinstance(value, str) else value
                return self._items[slice_parts[0]:slice_parts[1] + 1:key.step]
            return self._items[key]
        raise TypeError(f'Invalid key type: {type(key)}')

    def __find__(self, key: str) -> T:
        try:
            return next(item for item in self._items if item.__class__.__name__.lower() == key.lower())
        except StopIteration:
            raise KeyError(f"No item with class name '{key}' found.")

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