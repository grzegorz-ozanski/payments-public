""" Lookup list unittests."""
import pytest
from lookuplist.lookuplist import LookupList


class TestClass1:
    """ Mock class #1 """
    pass


class TestClass2:
    """ Mock class #2 """
    pass


def test_lookup_by_class_name() -> None:
    """Test that LookupList returns the correct item when indexed by class name."""
    lst = LookupList(TestClass1(), TestClass2())
    assert isinstance(lst["testclass1"], TestClass1)


def test_lookup_with_empty_string() -> None:
    """Test that LookupList returns itself when indexed with an empty string."""
    lst = LookupList(TestClass1(), TestClass2())
    assert lst[""] == lst


def test_lookup_with_wildcard() -> None:
    """Test that LookupList returns itself when indexed with a wildcard."""
    lst = LookupList(TestClass1(), TestClass2())
    assert lst["*"] == lst


def test_keyerror_for_invalid_class_name() -> None:
    """Test that LookupList raises KeyError for an invalid class name."""
    lst = LookupList(TestClass1(), TestClass2())
    with pytest.raises(KeyError, match="No item with class name 'invalidclass' found."):
        _ = lst["invalidclass"]


def test_typeerror_for_invalid_key_type() -> None:
    """Test that LookupList raises TypeError for invalid key types."""
    lst = LookupList(TestClass1(), TestClass2())
    with pytest.raises(TypeError, match="Invalid key type: <class 'float'>"):
        # noinspection PyTypeChecker
        _ = lst[3.14]


def test_slice_access() -> None:
    """Test that LookupList supports slicing."""
    lst = LookupList(TestClass1(), TestClass2())
    sliced_lst = lst[:1]
    assert isinstance(sliced_lst, list)
    assert len(sliced_lst) == 1
    assert isinstance(sliced_lst[0], TestClass1)


def test_lookup_contains_by_class_name() -> None:
    """Test that LookupList `in` works for class names."""
    lst = LookupList(TestClass1(), TestClass2())
    assert "testclass1" in lst
    assert "testclass2" in lst
    assert "invalidclass" not in lst


def test_lookup_contains_by_instance() -> None:
    """Test that LookupList `in` works for instances."""
    instance_1 = TestClass1()
    instance_2 = TestClass2()
    lst = LookupList(instance_1, instance_2)
    assert instance_1 in lst
    assert instance_2 in lst
    assert TestClass1() not in lst  # Different instance


def test_repr_output() -> None:
    """Test the string representation of LookupList."""
    lst = LookupList(TestClass1(), TestClass2())
    expected_repr = "<LookupList[TestClass1, TestClass2]>"
    assert repr(lst) == expected_repr
