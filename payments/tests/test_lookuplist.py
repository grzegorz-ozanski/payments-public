""" Lookup list unittests."""
from typing import Union

import pytest

from payments.lookuplist.lookuplist import LookupList


class TestClassBase:
    """ Base class for LookupList elements."""
    pass


TEST_CLASSES = [
    type(
        f"TestClass{i}",
        (TestClassBase,),
        {"__doc__": f"Mock class #{i}"},
    )
    for i in range(1, 6)
]

TestClass1, TestClass2, TestClass3, TestClass4, TestClass5 = TEST_CLASSES


def test_lookup_by_class_name() -> None:
    """Test that LookupList returns the correct item when indexed by class name."""
    lst = LookupList[TestClassBase](TestClass1(), TestClass2())
    assert isinstance(lst['testclass1'], TestClass1)


def test_lookup_contains_by_class_name() -> None:
    """Test that LookupList `in` works for class names."""
    lst = LookupList[Union[TestClassBase, str]](TestClass1(), TestClass2())
    assert 'testclass1' in lst
    assert 'testclass2' in lst
    assert 'invalidclass' not in lst


def test_lookup_contains_by_instance() -> None:
    """Test that LookupList `in` works for instances."""
    instance_1 = TestClass1()
    instance_2 = TestClass2()
    lst = LookupList[TestClassBase](instance_1, instance_2)
    assert instance_1 in lst
    assert instance_2 in lst
    assert TestClass1() not in lst  # Different instance


def test_lookup_with_empty_string() -> None:
    """Test that LookupList returns itself when indexed with an empty string."""
    lst = LookupList[TestClassBase](TestClass1(), TestClass2())
    assert lst[""] == lst


def test_lookup_with_wildcard() -> None:
    """Test that LookupList returns itself when indexed with a wildcard."""
    lst = LookupList[TestClassBase](TestClass1(), TestClass2())
    assert lst['*'] == lst


def test_keyerror_for_invalid_class_name() -> None:
    """Test that LookupList raises KeyError for an invalid class name."""
    lst = LookupList[TestClassBase](TestClass1(), TestClass2())
    with pytest.raises(KeyError, match="No item with class name 'invalidclass' found."):
        _ = lst['invalidclass']


def test_typeerror_for_invalid_key_type() -> None:
    """Test that LookupList raises TypeError for invalid key types."""
    lst = LookupList[TestClassBase](TestClass1(), TestClass2())
    with pytest.raises(TypeError, match="Invalid key type: <class 'float'>"):
        # noinspection PyTypeChecker
        # ignore mypy check as we actually want to call with the wrong key type
        _ = lst[3.14]  # type: ignore[call-overload]


def test_repr_output() -> None:
    """Test the string representation of LookupList."""
    lst = LookupList[TestClassBase](TestClass1(), TestClass2())
    expected_repr = '<LookupList[TestClass1, TestClass2]>'
    assert repr(lst) == expected_repr


def test_slice_access() -> None:
    """Test that LookupList supports slicing."""
    lst = LookupList[TestClassBase](TestClass1(), TestClass2())
    sliced_lst = lst[:1]
    assert isinstance(sliced_lst, list)
    assert len(sliced_lst) == 1
    assert isinstance(sliced_lst[0], TestClass1)


def test_prefix() -> None:
    """Test that LookupList supports prefixing."""
    lst = LookupList[Union[TestClassBase, str]](TestClass1(), TestClass2())
    item = lst['testclass*']
    assert isinstance(item, TestClass1)


def test_comma_separated() -> None:
    """Test that LookupList supports comma separated keys."""

    tcs: list[TestClassBase] = [
        cls() for cls in TEST_CLASSES if int(cls.__name__[-1]) < 4
    ]
    assert len(tcs) == 3
    lst = LookupList[Union[TestClassBase, str]](*tcs)
    sublist = lst['testclass1,testclass3']
    assert isinstance(sublist, list)
    assert tcs[0] in sublist
    assert tcs[2] in sublist
    assert tcs[1] not in sublist


def test_range() -> None:
    """Test that LookupList supports comma separated keys."""

    tcs: list[TestClassBase] = [
        cls() for cls in TEST_CLASSES
    ]
    lst = LookupList[Union[TestClassBase, str]](*tcs)
    sublist = lst['testclass2-testclass4']
    assert isinstance(sublist, list)
    assert tcs[0] not in sublist
    assert tcs[1] in sublist
    assert tcs[2] in sublist
    assert tcs[3] in sublist
    assert tcs[4] not in sublist
