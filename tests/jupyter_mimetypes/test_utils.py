# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Tests for utils module functions."""

import base64

import pandas as pd
import pytest

from jupyter_mimetypes._constants import _DEFAULT_ARROW_MIMETYPE, _DEFAULT_PICKLE_MIMETYPE
from jupyter_mimetypes._io._pickle import _deserialize_pickle, _serialize_pickle
from jupyter_mimetypes._proxy import _MIMETYPES as MIMETYPES
from jupyter_mimetypes._utils import (
    _format_object,
    _from_b64,
    _get_mimetype_funcs_for_obj,
    _get_mimetypes_funcs_for_mod_type,
    _get_serialized_type,
    _to_b64,
)


def test_get_serialized_type_dataframe():
    """Test get_serialized_type with pandas DataFrame."""
    df = pd.DataFrame({"a": [1, 2, 3]})
    module, name = _get_serialized_type(df)

    assert module == "pandas.core.frame"
    assert name == "DataFrame"


def test_get_serialized_type_series():
    """Test get_serialized_type with pandas Series."""
    series = pd.Series([1, 2, 3])
    module, name = _get_serialized_type(series)

    assert module == "pandas.core.series"
    assert name == "Series"


def test_get_serialized_type_builtin_types():
    """Test get_serialized_type with builtin types."""
    # Test list
    test_list = [1, 2, 3]
    module, name = _get_serialized_type(test_list)
    assert module == "builtins"
    assert name == "list"

    # Test dict
    test_dict = {"key": "value"}
    module, name = _get_serialized_type(test_dict)
    assert module == "builtins"
    assert name == "dict"

    # Test string
    test_str = "hello"
    module, name = _get_serialized_type(test_str)
    assert module == "builtins"
    assert name == "str"


def test_get_serialized_type_custom_class():
    """Test get_serialized_type with custom class."""

    class CustomClass:
        pass

    obj = CustomClass()
    module, name = _get_serialized_type(obj)

    assert module == "tests.jupyter_mimetypes.test_utils"  # Current module
    assert name == "test_get_serialized_type_custom_class.<locals>.CustomClass"


def test_get_serialized_type_none_module():
    """Test get_serialized_type with object having no module."""
    # Create an object type that might not have __module__
    obj = type("TestType", (), {})()
    module, name = _get_serialized_type(obj)

    # Should handle cases where module might be None
    assert isinstance(name, str)
    assert len(name) > 0


def test_format_object_basic(monkeypatch):
    """Test format_object with basic object."""

    # Create mock formatter functions
    def mock_text_formatter(obj):
        return "text representation"

    # Mock InteractiveShell and its components
    class MockFormatter:
        def __init__(self):
            self.formatters = {"text/plain": mock_text_formatter}

    class MockShell:
        def __init__(self):
            self.display_formatter = MockFormatter()

    def mock_instance():
        return MockShell()

    # Patch the InteractiveShell by importing and monkeypatching directly
    import IPython.core.interactiveshell

    monkeypatch.setattr(
        IPython.core.interactiveshell,
        "InteractiveShell",
        type("MockInteractiveShell", (), {"instance": staticmethod(mock_instance)}),
    )

    # Test function
    data, metadata = _format_object("test string")

    assert isinstance(data, dict)
    assert isinstance(metadata, dict)
    assert data.get("text/plain") == "text representation"


def test_format_object_with_include(monkeypatch):
    """Test format_object with include parameter."""

    # Create mock formatter functions
    def mock_text_formatter(obj):
        return "text representation"

    def mock_html_formatter(obj):
        return "<div>html</div>"

    # Mock InteractiveShell and its components
    class MockFormatter:
        def __init__(self):
            self.formatters = {
                "text/plain": mock_text_formatter,
                "text/html": mock_html_formatter,
            }

    class MockShell:
        def __init__(self):
            self.display_formatter = MockFormatter()

    def mock_instance():
        return MockShell()

    # Patch the InteractiveShell by importing and monkeypatching directly
    import IPython.core.interactiveshell

    monkeypatch.setattr(
        IPython.core.interactiveshell,
        "InteractiveShell",
        type("MockInteractiveShell", (), {"instance": staticmethod(mock_instance)}),
    )

    # Test with include set
    include_set = {"text/plain"}
    data, metadata = _format_object("test", include=include_set)

    # Only text/plain should be included
    assert "text/plain" in data
    assert "text/html" not in data


def test_format_object_with_exclude(monkeypatch):
    """Test format_object with exclude parameter."""

    # Create mock formatter functions
    def mock_text_formatter(obj):
        return "text representation"

    def mock_html_formatter(obj):
        return "<div>html</div>"

    # Mock InteractiveShell and its components
    class MockFormatter:
        def __init__(self):
            self.formatters = {
                "text/plain": mock_text_formatter,
                "text/html": mock_html_formatter,
            }

    class MockShell:
        def __init__(self):
            self.display_formatter = MockFormatter()

    def mock_instance():
        return MockShell()

    # Patch the InteractiveShell by importing and monkeypatching directly
    import IPython.core.interactiveshell

    monkeypatch.setattr(
        IPython.core.interactiveshell,
        "InteractiveShell",
        type("MockInteractiveShell", (), {"instance": staticmethod(mock_instance)}),
    )

    # Test with exclude set
    exclude_set = {"text/html"}
    data, metadata = _format_object("test", exclude=exclude_set)

    # Only text/plain should be included
    assert "text/plain" in data
    assert "text/html" not in data


def test_format_object_no_formatter(monkeypatch):
    """Test format_object when no display formatter is available."""

    class MockShell:
        def __init__(self):
            self.display_formatter = None

    def mock_instance():
        return MockShell()

    monkeypatch.setattr("IPython.core.interactiveshell.InteractiveShell.instance", mock_instance)

    data, metadata = _format_object("test")

    assert data == {}
    assert metadata == {}


def test_format_object_formatter_returns_tuple(monkeypatch):
    """Test format_object when formatter returns (data, metadata) tuple."""

    # Create mock formatter that returns tuple
    def mock_text_formatter(obj):
        return ("text data", {"key": "value"})

    # Mock InteractiveShell and its components
    class MockFormatter:
        def __init__(self):
            self.formatters = {"text/plain": mock_text_formatter}

    class MockShell:
        def __init__(self):
            self.display_formatter = MockFormatter()

    def mock_instance():
        return MockShell()

    # Patch the InteractiveShell by importing and monkeypatching directly
    import IPython.core.interactiveshell

    monkeypatch.setattr(
        IPython.core.interactiveshell,
        "InteractiveShell",
        type("MockInteractiveShell", (), {"instance": staticmethod(mock_instance)}),
    )

    # Test function
    data, metadata = _format_object("test")

    assert data["text/plain"] == "text data"
    assert metadata["text/plain"] == {"key": "value"}


def test_to_b64_basic():
    """Test to_b64 with basic binary data."""
    test_data = b"Hello, World!"
    encoded = _to_b64(test_data)

    assert isinstance(encoded, str)
    # Should be valid base64
    decoded = base64.b64decode(encoded.encode())
    assert decoded == test_data


def test_from_b64_basic():
    """Test from_b64 with basic base64 string."""
    original_data = b"Hello, World!"
    # Create base64 string
    b64_string = base64.b64encode(original_data).decode()

    decoded = _from_b64(b64_string)
    assert decoded == original_data


def test_roundtrip_b64_encoding():
    """Test roundtrip base64 encoding/decoding."""
    test_cases = [
        b"Simple string",
        b"String with special chars: \x00\x01\x02\x03",
        b"Unicode: \xc4\x85\xc4\x99\xc5\x82\xc5\x84",
        b"",  # Empty bytes
        bytes(range(256)),  # All possible byte values
    ]

    for original_data in test_cases:
        encoded = _to_b64(original_data)
        decoded = _from_b64(encoded)
        assert decoded == original_data


def test_b64_with_different_encodings():
    """Test base64 functions with different text encodings."""
    test_data = b"Test data with utf-8"

    # Test with utf-8 (default)
    encoded_utf8 = _to_b64(test_data, encoding="utf-8")
    decoded_utf8 = _from_b64(encoded_utf8, encoding="utf-8")
    assert decoded_utf8 == test_data

    # Test with ascii
    encoded_ascii = _to_b64(test_data, encoding="ascii")
    decoded_ascii = _from_b64(encoded_ascii, encoding="ascii")
    assert decoded_ascii == test_data


def test_get_mimetype_funcs_for_obj_dataframe():
    """Test get_mimetype_funcs_for_obj with DataFrame."""
    df = pd.DataFrame({"a": [1, 2, 3]})
    mimetype, serialize_func, deserialize_func = _get_mimetype_funcs_for_obj(df, MIMETYPES)

    assert mimetype == _DEFAULT_ARROW_MIMETYPE
    assert callable(serialize_func)
    assert callable(deserialize_func)


def test_get_mimetype_funcs_for_obj_series():
    """Test get_mimetype_funcs_for_obj with Series."""
    series = pd.Series([1, 2, 3])
    mimetype, serialize_func, deserialize_func = _get_mimetype_funcs_for_obj(series, MIMETYPES)

    assert mimetype == _DEFAULT_ARROW_MIMETYPE
    assert callable(serialize_func)
    assert callable(deserialize_func)


def test_get_mimetype_funcs_for_obj_generic():
    """Test get_mimetype_funcs_for_obj with generic object."""
    test_list = [1, 2, 3]
    mimetype, serialize_func, deserialize_func = _get_mimetype_funcs_for_obj(test_list, MIMETYPES)

    assert mimetype == _DEFAULT_PICKLE_MIMETYPE
    assert callable(serialize_func)
    assert callable(deserialize_func)


def test_get_mimetypes_funcs_for_mod_type_exact_match():
    """Test get_mimetypes_funcs_for_mod_type with exact match."""
    mimetype, serialize_func, deserialize_func = _get_mimetypes_funcs_for_mod_type(
        "pandas.core.frame", "DataFrame", MIMETYPES
    )

    assert mimetype == _DEFAULT_ARROW_MIMETYPE
    assert callable(serialize_func)
    assert callable(deserialize_func)


def test_get_mimetypes_funcs_for_mod_type_wildcard_match():
    """Test get_mimetypes_funcs_for_mod_type with wildcard match."""
    mimetype, serialize_func, deserialize_func = _get_mimetypes_funcs_for_mod_type(
        "some.unknown.module", "UnknownType", MIMETYPES
    )

    assert mimetype == _DEFAULT_PICKLE_MIMETYPE
    assert callable(serialize_func)
    assert callable(deserialize_func)


def test_get_mimetypes_funcs_for_mod_type_no_match():
    """Test get_mimetypes_funcs_for_mod_type with no match."""
    empty_mimetypes = {}
    mimetype, serialize_func, deserialize_func = _get_mimetypes_funcs_for_mod_type(
        "some.module", "SomeType", empty_mimetypes
    )

    assert mimetype is _DEFAULT_PICKLE_MIMETYPE
    assert serialize_func is _serialize_pickle
    assert deserialize_func is _deserialize_pickle


def test_get_mimetypes_funcs_for_mod_type_none_type():
    """Test get_mimetypes_funcs_for_mod_type with None type."""
    mimetype, serialize_func, deserialize_func = _get_mimetypes_funcs_for_mod_type(
        "some.module",
        "",
        MIMETYPES,
    )

    assert mimetype is _DEFAULT_PICKLE_MIMETYPE
    assert serialize_func is _serialize_pickle
    assert deserialize_func is _deserialize_pickle


def test_format_object_no_interactive_shell(monkeypatch):
    """Test format_object when InteractiveShell is not available."""

    def mock_instance():
        raise RuntimeError("No shell available")

    import IPython.core.interactiveshell

    monkeypatch.setattr(
        IPython.core.interactiveshell,
        "InteractiveShell",
        type("MockInteractiveShell", (), {"instance": staticmethod(mock_instance)}),
    )

    # Should handle missing InteractiveShell gracefully
    with pytest.raises(RuntimeError):
        _format_object("test")


def test_base64_encoding_edge_cases():
    """Test base64 encoding/decoding with edge cases."""
    edge_cases = [
        b"",  # Empty bytes
        b"\x00",  # Null byte
        b"\x00\x01\x02\x03\x04\x05",  # Binary data
        bytes(range(256)),  # All possible byte values
    ]

    for test_data in edge_cases:
        encoded = _to_b64(test_data)
        decoded = _from_b64(encoded)
        assert decoded == test_data


def test_get_serialized_type_edge_cases():
    """Test get_serialized_type with edge cases."""
    # Test with built-in types
    edge_cases = [
        None,
        ...,  # Ellipsis
        NotImplemented,
        type(lambda: None),  # Function type
        type,  # Type itself
    ]

    for obj in edge_cases:
        module, name = _get_serialized_type(obj)
        assert isinstance(name, str)
        assert len(name) > 0


def test_mimetype_lookup_edge_cases():
    """Test MIME type lookup functions with edge cases."""
    # Test with empty mimetypes mapping
    empty_mimetypes = {}
    mimetype, serialize_func, deserialize_func = _get_mimetype_funcs_for_obj(
        "test", empty_mimetypes
    )
    assert mimetype is _DEFAULT_PICKLE_MIMETYPE
    assert serialize_func is _serialize_pickle
    assert deserialize_func is _deserialize_pickle


def test_graceful_degradation(monkeypatch):
    """Test graceful degradation when optional components fail."""

    # This tests that the system continues to work even when some parts fail
    def mock_instance():
        raise ImportError("IPython not available")

    import IPython.core.interactiveshell

    monkeypatch.setattr(
        IPython.core.interactiveshell,
        "InteractiveShell",
        type("MockInteractiveShell", (), {"instance": staticmethod(mock_instance)}),
    )

    # Should still be able to format objects, but will raise the exception
    with pytest.raises(ImportError):
        _format_object({"key": "value"})
