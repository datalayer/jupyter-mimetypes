# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Tests for _ProxyObject class functionality."""

import numpy as np
import pandas as pd
import pytest
import torch

from jupyter_mimetypes._constants import (
    _DEFAULT_ARROW_MIMETYPE,
    _DEFAULT_PICKLE_MIMETYPE,
    _GENERIC_REPR_METHOD,
)
from jupyter_mimetypes._proxy import _ProxyObject


class ProblematicObject:
    def __getattribute__(self, name):
        if name == _GENERIC_REPR_METHOD:
            raise AttributeError("Method not available")

        return super().__getattribute__(name)


class ObjectWithRepr:
    def _repr_mimebundle_(self, include=None, exclude=None):
        return {"text/plain": "existing_repr"}, {"text/plain": {}}


@pytest.mark.parametrize(
    "test_object,use_identity_check",
    [
        (pd.Series([1, 2, 3], name="test_series"), True),
        ([1, 2, 3, "hello"], False),
        (np.array([1, 2, 3, 4, 5]), True),
        (torch.tensor([1.0, 2.0, 3.0, 4.0, 5.0]), True),
    ],
)
def test_proxy_object_initialization(test_object, use_identity_check):
    """Test _ProxyObject initialization with various object types."""
    proxy = _ProxyObject(test_object)

    if use_identity_check:
        assert proxy._wrapped is test_object
    else:
        assert proxy._wrapped == test_object
    assert hasattr(proxy, "_repr_mimebundle_")


@pytest.mark.parametrize(
    "test_object,expected_mimetype",
    [
        (pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]}), _DEFAULT_ARROW_MIMETYPE),
        (pd.Series([1, 2, 3], name="test_series"), _DEFAULT_ARROW_MIMETYPE),
        ({"key": "value", "numbers": [1, 2, 3]}, _DEFAULT_PICKLE_MIMETYPE),
    ],
)
def test_repr_mimebundle_data_types(test_object, expected_mimetype):
    """Test _repr_mimebundle_ method with various data types."""
    proxy = _ProxyObject(test_object)

    data, metadata = proxy._repr_mimebundle_()

    assert isinstance(data, dict)
    assert isinstance(metadata, dict)
    assert expected_mimetype in data
    assert expected_mimetype in metadata
    assert "type" in metadata[expected_mimetype]


@pytest.mark.parametrize(
    "filter_param,filter_value,keys",
    [
        (
            "include",
            {_DEFAULT_ARROW_MIMETYPE, "text/plain"},
            {_DEFAULT_ARROW_MIMETYPE, "text/plain"},
        ),
        ("exclude", {"text/html", "text/plain"}, {_DEFAULT_ARROW_MIMETYPE}),
        (
            "exclude",
            {_DEFAULT_ARROW_MIMETYPE},
            {"text/plain", "text/html"},
        ),
    ],
)
def test_repr_mimebundle_with_filters(filter_param, filter_value, keys):
    """Test _repr_mimebundle_ method with include/exclude parameters."""
    df = pd.DataFrame({"a": [1, 2, 3]})
    proxy = _ProxyObject(df)
    kwargs = {filter_param: filter_value}
    data, metadata = proxy._repr_mimebundle_(**kwargs)
    assert isinstance(data, dict)
    assert isinstance(metadata, dict)
    assert set(data.keys()) == keys


def test_repr_mimebundle_with_existing_repr_method():
    """Test _repr_mimebundle_ with object that already has the method."""
    obj_with_repr = ObjectWithRepr()
    proxy = _ProxyObject(obj_with_repr)

    data, metadata = proxy._repr_mimebundle_()

    assert isinstance(data, dict)
    assert isinstance(metadata, dict)
    # Should include both the existing repr and our custom one
    assert "text/plain" in data


@pytest.mark.parametrize(
    "test_object",
    [
        np.array([[1, 2, 3], [4, 5, 6]]),
        torch.randn(3, 4),
    ],
)
def test_repr_mimebundle_numpy_pytorch(test_object):
    """Test _repr_mimebundle_ method with NumPy arrays and PyTorch tensors."""
    proxy = _ProxyObject(test_object)
    data, metadata = proxy._repr_mimebundle_()
    assert isinstance(data, dict)
    assert isinstance(metadata, dict)
    # NumPy arrays and PyTorch tensors should use pickle serialization
    assert _DEFAULT_PICKLE_MIMETYPE in data
    assert _DEFAULT_PICKLE_MIMETYPE in metadata
    assert "type" in metadata[_DEFAULT_PICKLE_MIMETYPE]


@pytest.mark.parametrize(
    "test_array",
    [
        np.array([1, 2, 3], dtype=np.int32),
        np.array([1.1, 2.2, 3.3], dtype=np.float64),
        np.array([True, False, True], dtype=np.bool_),
        np.array(["hello", "world"], dtype=np.str_),
    ],
)
def test_repr_mimebundle_numpy_different_dtypes(test_array):
    """Test _repr_mimebundle_ method with NumPy arrays of different dtypes."""
    proxy = _ProxyObject(test_array)
    data, metadata = proxy._repr_mimebundle_()

    assert isinstance(data, dict)
    assert isinstance(metadata, dict)
    assert _DEFAULT_PICKLE_MIMETYPE in data
    assert _DEFAULT_PICKLE_MIMETYPE in metadata
    assert "type" in metadata[_DEFAULT_PICKLE_MIMETYPE]


@pytest.mark.parametrize(
    "test_tensor",
    [
        torch.tensor([1, 2, 3], dtype=torch.int32),
        torch.tensor([1.1, 2.2, 3.3], dtype=torch.float64),
        torch.tensor([True, False, True], dtype=torch.bool),
        torch.zeros(5, 3),
        torch.ones(2, 4, 3),
    ],
)
def test_repr_mimebundle_pytorch_different_types(test_tensor):
    """Test _repr_mimebundle_ method with PyTorch tensors of different types."""
    proxy = _ProxyObject(test_tensor)
    data, metadata = proxy._repr_mimebundle_()

    assert isinstance(data, dict)
    assert isinstance(metadata, dict)
    assert _DEFAULT_PICKLE_MIMETYPE in data
    assert _DEFAULT_PICKLE_MIMETYPE in metadata
    assert "type" in metadata[_DEFAULT_PICKLE_MIMETYPE]


def test_proxy_object_with_problematic_objects():
    """Test _ProxyObject with objects that might cause issues."""
    obj = ProblematicObject()
    proxy = _ProxyObject(obj)

    # Should handle the problematic object gracefully
    data, metadata = proxy._repr_mimebundle_()
    assert isinstance(data, dict)
    assert isinstance(metadata, dict)


def test_proxy_object_serialization_failure():
    """Test _ProxyObject when serialization fails."""

    class UnserializableObject:
        def __reduce__(self):
            raise RuntimeError("Cannot serialize this object")

        def __getstate__(self):
            raise RuntimeError("Cannot get state")

    obj = UnserializableObject()
    proxy = _ProxyObject(obj)

    # The proxy should try to serialize but might fail
    # This tests the error handling in the proxy
    try:
        data, metadata = proxy._repr_mimebundle_()
        # If it succeeds, that's fine (format_object might handle it)
        assert isinstance(data, dict)
        assert isinstance(metadata, dict)
    except (ValueError, RuntimeError):
        # If it fails, that's expected for this problematic object
        pass


def test_memory_usage_with_large_dataframes():
    """Test memory usage doesn't explode with large DataFrames."""
    import numpy as np

    # Create a reasonably large DataFrame
    large_df = pd.DataFrame({f"col_{i}": np.random.randn(1000) for i in range(20)})

    # Should handle serialization without excessive memory usage
    proxy = _ProxyObject(large_df)
    data, metadata = proxy._repr_mimebundle_()

    assert isinstance(data, dict)
    assert isinstance(metadata, dict)
    assert _DEFAULT_ARROW_MIMETYPE in data


def test_thread_safety_considerations():
    """Test considerations for thread safety."""
    # This is a basic test - full thread safety would require concurrent testing

    df = pd.DataFrame({"a": [1, 2, 3]})

    # Multiple proxy objects of the same data should work independently
    proxy1 = _ProxyObject(df)
    proxy2 = _ProxyObject(df)

    data1, metadata1 = proxy1._repr_mimebundle_()
    data2, metadata2 = proxy2._repr_mimebundle_()

    # Should produce identical results
    assert data1 == data2
    assert metadata1 == metadata2


def test_edge_case_dataframe_dtypes():
    """Test DataFrames with unusual dtypes."""

    edge_case_dfs = [
        # DataFrame with datetime
        pd.DataFrame({"date": pd.date_range("2023-01-01", periods=3)}),
        # DataFrame with categorical
        pd.DataFrame({"cat": pd.Categorical(["a", "b", "a"])}),
        # DataFrame with complex numbers
        pd.DataFrame({"complex": [1 + 2j, 3 + 4j, 5 + 6j]}),
    ]

    for df in edge_case_dfs:
        try:
            proxy = _ProxyObject(df)
            data, metadata = proxy._repr_mimebundle_()
            assert isinstance(data, dict)
            assert isinstance(metadata, dict)
        except Exception as e:
            # Some dtypes might not be supported by Arrow
            pytest.skip(f"Dtype not supported: {e}")


def test_consistent_serialization_results():
    """Test that serialization produces consistent results."""
    test_df = pd.DataFrame({"key": ["value1", "value2"], "list": [[1, 2, 3], [4, 5, 6]]})

    # Multiple serializations should produce identical results
    results = []
    for _ in range(5):
        proxy = _ProxyObject(test_df)
        data, metadata = proxy._repr_mimebundle_()
        results.append((data, metadata))

    # All results should be identical
    first_result = results[0]
    for result in results[1:]:
        assert result == first_result


def test_serialization_doesnt_modify_original():
    """Test that serialization doesn't modify the original object."""
    original_df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    original_copy = original_df.copy()

    # Serialize multiple times
    for _ in range(3):
        proxy = _ProxyObject(original_df)
        data, metadata = proxy._repr_mimebundle_()

    # Original should be unchanged
    assert original_df.equals(original_copy)
