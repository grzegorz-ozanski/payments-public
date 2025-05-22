from typing import Any, overload, Union


class LookupList(list):
    """
    List extension, allowing indexing by class name of the list item

    Przykład:
        lst = LookupList(Class1(), Class1(), Class2())
        lst['class1']  # -> same as lst[0]
        lst['']        # -> same as lst
    """

    def __init__(self, *items: Any) -> None:
        super().__init__(items)

    @overload
    def __getitem__(self, key: int) -> Any:
        ...

    @overload
    def __getitem__(self, key: slice) -> list[Any]:
        ...

    @overload
    def __getitem__(self, key: str) -> Union[Any, 'LookupList']:
        ...

    def __getitem__(self, key: object) -> Any:
        if isinstance(key, str):
            if key == '' or key == '*':
                return self
            try:
                return next(item for item in self if getattr(item, '__class__', None).__name__.lower() == key.lower())
            except StopIteration:
                raise KeyError(f"No item with class name '{key}' found.")
        if isinstance(key, (int, slice)):
            return super().__getitem__(key)
        raise TypeError(f"Invalid key type: {type(key)}")

    def __contains__(self, key: object) -> bool:
        if isinstance(key, str):
            return any(getattr(item, '__class__', None).__name__.lower() == key.lower() for item in self)
        return super().__contains__(key)

    def __repr__(self) -> str:
        return f"<LookupList[{', '.join(item.__class__.__name__ for item in self)}]>"
