# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Tests for IO serialization functions."""

from typing import Any

import numpy as np
import pandas as pd
import pytest

from jupyter_mimetypes._constants import _DEFAULT_ARROW_MIMETYPE, _DEFAULT_PICKLE_MIMETYPE
from jupyter_mimetypes._io._api import _deserialize, _serialize
from jupyter_mimetypes._proxy import _MIMETYPES as MIMETYPES


def test_serialize_dataframe():
    """Test serialize function with pandas DataFrame."""
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})

    serialized_data, mimetype = _serialize(df, MIMETYPES)

    assert isinstance(serialized_data, str)  # base64 encoded
    assert mimetype == _DEFAULT_ARROW_MIMETYPE
    assert len(serialized_data) > 0


def test_serialize_series():
    """Test serialize function with pandas Series."""
    series = pd.Series([1, 2, 3], name="test_series")

    serialized_data, mimetype = _serialize(series, MIMETYPES)

    assert isinstance(serialized_data, str)  # base64 encoded
    assert mimetype == _DEFAULT_ARROW_MIMETYPE
    assert len(serialized_data) > 0


def test_serialize_generic_object():
    """Test serialize function with generic Python object."""
    test_dict = {"key": "value", "numbers": [1, 2, 3]}

    serialized_data, mimetype = _serialize(test_dict, MIMETYPES)

    assert isinstance(serialized_data, str)  # base64 encoded
    assert mimetype == _DEFAULT_PICKLE_MIMETYPE
    assert len(serialized_data) > 0


def test_serialize_various_types():
    """Test serialize function with various Python types."""
    test_cases = [
        ([1, 2, 3, "hello"], _DEFAULT_PICKLE_MIMETYPE),
        ({"nested": {"dict": "value"}}, _DEFAULT_PICKLE_MIMETYPE),
        ("simple string", _DEFAULT_PICKLE_MIMETYPE),
        (42, _DEFAULT_PICKLE_MIMETYPE),
        (3.14159, _DEFAULT_PICKLE_MIMETYPE),
    ]

    for obj, expected_mimetype in test_cases:
        serialized_data, mimetype = _serialize(obj, MIMETYPES)
        assert isinstance(serialized_data, str)
        assert mimetype == expected_mimetype
        assert len(serialized_data) > 0


def test_deserialize_dataframe():
    """Test deserialize function with pandas DataFrame data."""
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})

    # First serialize
    serialized_data, mimetype = _serialize(df, MIMETYPES)

    # Then deserialize
    metadata = {_DEFAULT_ARROW_MIMETYPE: {"type": ("pandas.core.frame", "DataFrame")}}
    restored_df = _deserialize(serialized_data, MIMETYPES, metadata, mimetype)

    assert isinstance(restored_df, pd.DataFrame)
    assert restored_df.equals(df)


def test_deserialize_series():
    """Test deserialize function with pandas Series data."""
    series = pd.Series([1, 2, 3], name="test_series")

    # First serialize
    serialized_data, mimetype = _serialize(series, MIMETYPES)

    # Then deserialize
    metadata = {_DEFAULT_ARROW_MIMETYPE: {"type": ("pandas.core.series", "Series")}}
    restored_series = _deserialize(serialized_data, MIMETYPES, metadata, mimetype)

    assert isinstance(restored_series, pd.Series)
    assert restored_series.equals(series)


def test_deserialize_generic_object():
    """Test deserialize function with generic Python object."""
    test_dict = {"key": "value", "numbers": [1, 2, 3]}

    # First serialize
    serialized_data, mimetype = _serialize(test_dict, MIMETYPES)

    # Then deserialize
    metadata = {_DEFAULT_PICKLE_MIMETYPE: {"type": ("builtins", "dict")}}
    restored_dict = _deserialize(serialized_data, MIMETYPES, metadata, mimetype)

    assert isinstance(restored_dict, dict)
    assert restored_dict == test_dict


def test_deserialize_various_types():
    """Test deserialize function with various Python types."""
    test_cases = [
        ([1, 2, 3, "hello"], "list"),
        ({"nested": {"dict": "value"}}, "dict"),
        ("simple string", "str"),
        (42, "int"),
        (3.14159, "float"),
        ((1, 2, 3), "tuple"),
        ({1, 2, 3}, "set"),
    ]

    for original_obj, var_type in test_cases:
        serialized_data, mimetype = _serialize(original_obj, MIMETYPES)
        metadata = {_DEFAULT_PICKLE_MIMETYPE: {"type": ("builtins", var_type)}}
        restored_obj = _deserialize(serialized_data, MIMETYPES, metadata, mimetype)

        assert restored_obj == original_obj
        assert type(restored_obj) is type(original_obj)


def test_deserialize_default_mimetype():
    """Test deserialize function with default mimetype."""
    test_obj = {"key": "value"}

    # Serialize with default (pickle) mimetype
    serialized_data, _ = _serialize(test_obj, MIMETYPES)

    # Deserialize without specifying mimetype (should default to pickle)
    metadata = {}
    restored_obj = _deserialize(serialized_data, MIMETYPES, metadata)

    assert restored_obj == test_obj


def test_deserialize_unsupported_mimetype():
    """Test deserialize function with unsupported mimetype."""
    metadata = {}
    with pytest.raises(ValueError):
        _deserialize("some_data", MIMETYPES, metadata, "unsupported/mimetype")


def test_deserialize_invalid_data():
    """Test deserialize function with invalid base64 data."""
    metadata = {}
    with pytest.raises(ValueError, match="Deserialization failed"):
        _deserialize("invalid_base64_data", MIMETYPES, metadata, _DEFAULT_PICKLE_MIMETYPE)


def test_deserialize_corrupted_data():
    """Test deserialize function with corrupted but valid base64 data."""
    # Create valid base64 but invalid pickle data
    import base64

    corrupted_data = base64.b64encode(b"corrupted_pickle_data").decode()
    metadata = {}
    with pytest.raises(ValueError, match="Deserialization failed"):
        _deserialize(corrupted_data, MIMETYPES, metadata, _DEFAULT_PICKLE_MIMETYPE)


def test_roundtrip_serialization_dataframe():
    """Test complete roundtrip serialization for DataFrame."""
    original_df = pd.DataFrame(
        {
            "integers": [1, 2, 3, 4, 5],
            "floats": [1.1, 2.2, 3.3, 4.4, 5.5],
            "strings": ["a", "b", "c", "d", "e"],
            "booleans": [True, False, True, False, True],
        }
    )

    # Serialize
    serialized_data, mimetype = _serialize(original_df, MIMETYPES)

    # Deserialize
    metadata = {_DEFAULT_ARROW_MIMETYPE: {"type": ("pandas.core.frame", "DataFrame")}}
    restored_df = _deserialize(serialized_data, MIMETYPES, metadata, mimetype)

    # Verify
    assert isinstance(restored_df, pd.DataFrame)
    assert restored_df.equals(original_df)
    assert list(restored_df.columns) == list(original_df.columns)
    assert restored_df.dtypes.equals(original_df.dtypes)


def test_roundtrip_serialization_series():
    """Test complete roundtrip serialization for Series."""
    original_series = pd.Series(
        [1, 2, 3, 4, 5], name="test_series", index=["a", "b", "c", "d", "e"]
    )

    # Serialize
    serialized_data, mimetype = _serialize(original_series, MIMETYPES)

    # Deserialize
    metadata = {_DEFAULT_ARROW_MIMETYPE: {"type": ("pandas.core.series", "Series")}}
    restored_series = _deserialize(serialized_data, MIMETYPES, metadata, mimetype)

    # Verify
    assert isinstance(restored_series, pd.Series)
    assert restored_series.equals(original_series)
    assert restored_series.name == original_series.name
    assert list(restored_series.index) == list(original_series.index)


def test_roundtrip_serialization_complex_objects():
    """Test roundtrip serialization with complex nested objects."""
    complex_obj = {
        "lists": [[1, 2, 3], ["a", "b", "c"]],
        "nested_dict": {
            "inner_list": [{"key": "value"}, {"key2": "value2"}],
            "inner_number": 42,
        },
        "tuple": (1, 2, "three"),
        "set": {1, 2, 3},
    }

    # Serialize
    serialized_data, mimetype = _serialize(complex_obj, MIMETYPES)

    # Deserialize
    metadata = {_DEFAULT_PICKLE_MIMETYPE: {"type": ("builtins", "dict")}}
    restored_obj = _deserialize(serialized_data, MIMETYPES, metadata, mimetype)

    # Verify structure (sets might have different order)
    assert isinstance(restored_obj, dict)
    assert restored_obj["lists"] == complex_obj["lists"]
    assert restored_obj["nested_dict"] == complex_obj["nested_dict"]
    assert restored_obj["tuple"] == complex_obj["tuple"]
    assert restored_obj["set"] == complex_obj["set"]


def test_serialize_deserialize_empty_objects():
    """Test serialization/deserialization of empty objects."""
    empty_objects = [
        (pd.DataFrame(), (_DEFAULT_ARROW_MIMETYPE, "pandas.core.frame", "DataFrame")),
        (pd.Series([], dtype=object), (_DEFAULT_ARROW_MIMETYPE, "pandas.core.series", "Series")),
        ({}, (_DEFAULT_PICKLE_MIMETYPE, "builtins", "dict")),
        ([], (_DEFAULT_PICKLE_MIMETYPE, "builtins", "list")),
        ("", (_DEFAULT_PICKLE_MIMETYPE, "builtins", "str")),
    ]

    for empty_obj, (mime, mod, var_type) in empty_objects:
        # Serialize
        serialized_data, mimetype = _serialize(empty_obj, MIMETYPES)

        # Deserialize
        metadata = {mime: {"type": (mod, var_type)}}
        restored_obj = _deserialize(serialized_data, MIMETYPES, metadata, mimetype)

        # Verify based on type
        if isinstance(empty_obj, pd.DataFrame):
            assert isinstance(restored_obj, pd.DataFrame)
            assert len(restored_obj) == 0
        elif isinstance(empty_obj, pd.Series):
            assert isinstance(restored_obj, pd.Series)
            assert len(restored_obj) == 0
        else:
            assert restored_obj == empty_obj
            assert type(restored_obj) is type(empty_obj)


def test_serialize_large_dataframe():
    """Test serialization of larger DataFrame."""
    # Create a larger DataFrame
    large_df = pd.DataFrame({f"col_{i}": np.random.randn(1000) for i in range(10)})

    # Serialize
    serialized_data, mimetype = _serialize(large_df, MIMETYPES)

    # Deserialize
    metadata = {_DEFAULT_ARROW_MIMETYPE: {"type": ("pandas.core.frame", "DataFrame")}}
    restored_df = _deserialize(serialized_data, MIMETYPES, metadata, mimetype)

    # Verify
    assert isinstance(restored_df, pd.DataFrame)
    assert restored_df.shape == large_df.shape
    assert list(restored_df.columns) == list(large_df.columns)
    # Use np.allclose for floating point comparison
    assert np.allclose(restored_df.values, large_df.values)


def test_serialize_very_large_object():
    """Test serialization with very large objects."""
    # Create a large object that might stress the serialization system
    large_data = {f"key_{i}": list(range(100)) for i in range(100)}

    # Should handle large objects
    serialized_data, mimetype = _serialize(large_data, MIMETYPES)
    assert isinstance(serialized_data, str)
    assert len(serialized_data) > 0

    # Should be able to deserialize
    metadata = {}
    restored = _deserialize(serialized_data, MIMETYPES, metadata, mimetype)
    assert isinstance(restored, dict)
    assert len(restored) == 100


def test_invalid_mimetype_in_mimetypes_mapping():
    """Test behavior with invalid entries in MIMETYPES mapping."""
    # Create a mapping with invalid serialization functions
    invalid_mimetypes: dict[tuple[str, str], tuple[str, Any, Any]] = {
        ("test.module", "TestClass"): (
            "application/test",
            None,  # Invalid serialization function
            lambda x: x,  # Valid deserialization function
        )
    }

    class TestClass:
        pass

    obj = TestClass()

    with pytest.raises((ValueError, TypeError)):
        _serialize(obj, invalid_mimetypes)
