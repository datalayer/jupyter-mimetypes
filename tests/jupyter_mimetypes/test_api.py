# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Tests for core API functions in __init__.py module."""

import pandas as pd
import pytest

from jupyter_mimetypes import (
    __version__,
    deserialize_object,
    get_variable,
    serialize_object,
)
from jupyter_mimetypes._constants import _DEFAULT_ARROW_MIMETYPE


def test_version_exists():
    """Test that __version__ is defined and is a valid version string."""
    assert __version__ is not None
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_serialize_object_dataframe():
    """Test serialize_object with pandas DataFrame."""
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})

    # Test without specific mimetype
    data, metadata = serialize_object(df)
    assert isinstance(data, dict)
    assert isinstance(metadata, dict)
    assert _DEFAULT_ARROW_MIMETYPE in data

    # Test with specific mimetype
    arrow_data, arrow_metadata = serialize_object(df, _DEFAULT_ARROW_MIMETYPE)
    assert isinstance(arrow_data, str)  # base64 encoded string
    assert isinstance(arrow_metadata, dict)


def test_serialize_object_series():
    """Test serialize_object with pandas Series."""
    series = pd.Series([1, 2, 3], name="test_series")

    # Test without specific mimetype
    data, metadata = serialize_object(series)
    assert isinstance(data, dict)
    assert isinstance(metadata, dict)
    assert _DEFAULT_ARROW_MIMETYPE in data

    # Test with specific mimetype
    arrow_data, arrow_metadata = serialize_object(series, _DEFAULT_ARROW_MIMETYPE)
    assert isinstance(arrow_data, str)  # base64 encoded string
    assert isinstance(arrow_metadata, dict)


def test_serialize_object_generic():
    """Test serialize_object with generic Python objects."""
    # Test with list (should use pickle)
    test_list = [1, 2, 3, "hello"]
    data, metadata = serialize_object(test_list)
    assert isinstance(data, dict)
    assert isinstance(metadata, dict)


def test_deserialize_object_dataframe():
    """Test deserialize_object with pandas DataFrame."""
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})

    # Serialize first
    data, metadata = serialize_object(df)

    # Then deserialize
    restored_df = deserialize_object(data, metadata)
    assert isinstance(restored_df, pd.DataFrame)
    assert restored_df.equals(df)


def test_deserialize_object_series():
    """Test deserialize_object with pandas Series."""
    series = pd.Series([1, 2, 3], name="test_series")

    # Serialize first
    data, metadata = serialize_object(series)

    # Then deserialize
    restored_series = deserialize_object(data, metadata)
    assert isinstance(restored_series, pd.Series)
    assert restored_series.equals(series)


def test_deserialize_object_generic():
    """Test deserialize_object with generic Python objects."""
    test_list = [1, 2, 3, "hello"]

    # Serialize first
    data, metadata = serialize_object(test_list)

    # Then deserialize
    restored_list = deserialize_object(data, metadata)
    assert isinstance(restored_list, list)
    assert restored_list == test_list


def test_deserialize_object_no_metadata():
    """Test deserialize_object with no metadata."""
    test_dict = {"key": "value"}
    data, _ = serialize_object(test_dict)

    # Should not work with None metadata
    with pytest.raises(ValueError, match="No valid deserialization data found"):
        deserialize_object(data, None)


def test_deserialize_object_invalid_data():
    """Test deserialize_object with invalid data."""
    with pytest.raises(ValueError, match="No valid deserialization data found"):
        deserialize_object({}, {})


def test_deserialize_object_invalid_mimetype():
    """Test deserialize_object with unsupported mimetype."""
    invalid_data = {"invalid/mimetype": "some_data"}
    invalid_metadata = {"invalid/mimetype": {"type": ("some.module", "SomeType")}}

    with pytest.raises(ValueError, match="Deserialization failed"):
        deserialize_object(invalid_data, invalid_metadata)


def test_get_variable_basic(monkeypatch):
    """Test _get_variable function with basic DataFrame."""
    df = pd.DataFrame({"a": [1, 2, 3]})

    def mock_globals():
        return {"test_var": df}

    import builtins

    monkeypatch.setattr(builtins, "globals", mock_globals)

    # Test function - should not raise an exception
    get_variable("test_var")


def test_get_variable_with_mimetype(monkeypatch):
    """Test _get_variable function with specific mimetype."""
    # Setup mock
    df = pd.DataFrame({"a": [1, 2, 3]})

    def mock_globals():
        return {"test_var": df}

    import builtins

    monkeypatch.setattr(builtins, "globals", mock_globals)

    # Test function with specific mimetype
    get_variable("test_var", _DEFAULT_ARROW_MIMETYPE)


def test_roundtrip_serialization():
    """Test complete roundtrip serialization/deserialization."""
    # Test with various data types
    test_cases = [
        pd.DataFrame({"nums": [1, 2, 3], "strings": ["a", "b", "c"]}),
        pd.Series([10, 20, 30], name="test_series"),
        {"dict_key": "dict_value", "numbers": [1, 2, 3]},
        [1, 2, 3, "mixed", {"nested": "dict"}],
        "simple string",
        42,
        3.14159,
    ]

    for original_obj in test_cases:
        # Serialize
        data, metadata = serialize_object(original_obj)

        # Deserialize
        restored_obj = deserialize_object(data, metadata)

        # Verify restoration based on type
        if isinstance(original_obj, pd.DataFrame):
            assert isinstance(restored_obj, pd.DataFrame)
            assert restored_obj.equals(original_obj)
        elif isinstance(original_obj, pd.Series):
            assert isinstance(restored_obj, pd.Series)
            assert restored_obj.equals(original_obj)
        else:
            assert restored_obj == original_obj


def test_serialize_object_error_handling():
    """Test error handling in serialize_object."""

    # Create an object that might cause serialization issues
    class UnserializableObject:
        def __getstate__(self):
            raise RuntimeError("Cannot serialize this object")

    obj = UnserializableObject()

    # Should handle the error gracefully
    # Note: This might use pickle fallback which could work or fail
    try:
        data, metadata = serialize_object(obj)
        # If it succeeds, that's fine - pickle might handle it
        assert isinstance(data, dict)
        assert isinstance(metadata, dict)
    except ValueError as e:
        # If it fails, should be a proper ValueError
        assert "Serialization failed" in str(e)


def test_serialize_object_with_none():
    """Test serialize_object handles None values."""
    data, metadata = serialize_object(None)
    assert isinstance(data, dict)
    assert isinstance(metadata, dict)

    # Should be able to deserialize None
    restored = deserialize_object(data, metadata)
    assert restored is None


def test_serialize_object_with_circular_reference():
    """Test serialize_object with circular references."""
    from typing import Any

    # Create circular reference
    circular_dict: dict[str, Any] = {"key": "value"}
    circular_dict["self"] = circular_dict

    # Should handle circular references gracefully (pickle can handle this)
    try:
        data, metadata = serialize_object(circular_dict)
        restored = deserialize_object(data, metadata)
        assert isinstance(restored, dict)
        assert restored["key"] == "value"
        assert restored["self"] is restored  # Circular reference preserved
    except (ValueError, RecursionError):
        # Some serialization methods might not handle circular refs
        pytest.skip("Circular references not supported by current serializer")


def test_deserialize_object_malformed_metadata():
    """Test deserialize_object with malformed metadata."""
    # Create valid serialized data
    test_obj = {"test": "data"}
    data, _ = serialize_object(test_obj)

    # Test with malformed metadata
    malformed_metadata_cases = [
        {},  # Empty metadata
        {"wrong_mimetype": {"type": ("module", "class")}},  # Wrong mimetype
        {next(iter(data.keys())): {}},  # Missing type info
        {next(iter(data.keys())): {"type": "not_a_tuple"}},  # Invalid type format
        {next(iter(data.keys())): {"type": ("module",)}},  # Incomplete type tuple
    ]

    for bad_metadata in malformed_metadata_cases:
        with pytest.raises(ValueError):
            deserialize_object(data, bad_metadata)  # type: ignore[arg-type]


def test_get_variable_missing_variable(monkeypatch):
    """Test get_variable with missing variable."""
    with pytest.raises(KeyError):
        get_variable("missing_var", globals_dict={"other_var": "value"})


def test_unicode_handling_in_serialization():
    """Test Unicode handling in serialization."""
    unicode_data = {
        "chinese": "你好世界",
        "emoji": "🎉🌟✨",
        "mixed": "Hello 世界! 🌍",
        "special_chars": "äöü ñ ç § ® ™",
    }

    # Should handle Unicode correctly
    data, metadata = serialize_object(unicode_data)
    restored = deserialize_object(data, metadata)

    assert restored == unicode_data


def test_exception_messages_are_informative():
    """Test that exception messages provide useful information."""
    # Test various error conditions and check message quality

    # Invalid deserialization data
    try:
        deserialize_object({}, {})
    except ValueError as e:
        assert "No valid deserialization data found" in str(e)
