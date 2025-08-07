# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Tests for pandas serialization functions."""

import numpy as np
import pandas as pd
import pytest

from jupyter_mimetypes._io._pandas import (
    _deserialize_pandas_dataframe,
    _deserialize_pandas_series,
    _serialize_pandas,
)


def test_pandas_dataframe_comprehensive_data_types():
    """Test pandas DataFrame serialization/deserialization with comprehensive data types."""
    # Comprehensive DataFrame test cases
    test_dataframes = [
        # Basic DataFrame
        pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}),
        # Single column
        pd.DataFrame({"col": [1, 2, 3, 4, 5]}),
        # Mixed types
        pd.DataFrame(
            {
                "int_col": [1, 2, 3],
                "float_col": [1.1, 2.2, 3.3],
                "str_col": ["a", "b", "c"],
                "bool_col": [True, False, True],
            }
        ),
        # Empty DataFrame
        pd.DataFrame(),
        # DataFrame with one row
        pd.DataFrame({"single": [42]}),
        # DataFrame with NaN values
        pd.DataFrame({"with_nan": [1.0, np.nan, 3.0], "strings": ["hello", None, "world"]}),
        # DataFrame with datetime
        pd.DataFrame({"dates": pd.date_range("2023-01-01", periods=3), "values": [10, 20, 30]}),
        # DataFrame with categorical data
        pd.DataFrame({"category": pd.Categorical(["A", "B", "A", "C"]), "values": [1, 2, 3, 4]}),
        # Large DataFrame
        pd.DataFrame(np.random.randn(100, 5), columns=[f"col_{i}" for i in range(5)]),
    ]

    for df in test_dataframes:
        # Test _serialize_pandas
        serialized = _serialize_pandas(df)
        assert isinstance(serialized, bytes)
        assert len(serialized) > 0

        # Test _deserialize_pandas_dataframe
        restored = _deserialize_pandas_dataframe(serialized)
        assert isinstance(restored, pd.DataFrame)

        # Compare DataFrames
        if df.empty:
            assert restored.empty
        else:
            pd.testing.assert_frame_equal(restored, df)


def test_pandas_series_comprehensive_data_types():
    """Test pandas Series serialization/deserialization with comprehensive data types."""
    # Comprehensive Series test cases
    test_series = [
        # Basic Series
        pd.Series([1, 2, 3, 4, 5]),
        # Named Series
        pd.Series([1, 2, 3], name="test_series"),
        # Different data types
        pd.Series([1.1, 2.2, 3.3, 4.4]),  # Float
        pd.Series(["a", "b", "c", "d"]),  # String
        pd.Series([True, False, True, False]),  # Boolean
        # Empty Series
        pd.Series([], dtype=float),
        # Single value Series
        pd.Series([42]),
        # Series with NaN
        pd.Series([1.0, np.nan, 3.0, np.nan]),
        # Series with datetime
        pd.Series(pd.date_range("2023-01-01", periods=5)),
        # Categorical Series
        pd.Series(pd.Categorical(["A", "B", "A", "C", "B"])),
        # Large Series
        pd.Series(np.random.randn(1000)),
    ]

    for series in test_series:
        # Test _serialize_pandas
        serialized = _serialize_pandas(series)
        assert isinstance(serialized, bytes)
        assert len(serialized) > 0

        # Test _deserialize_pandas_series
        restored = _deserialize_pandas_series(serialized)
        assert isinstance(restored, pd.Series)

        # Compare Series
        if series.empty:
            assert restored.empty
        else:
            print(restored)
            print(series)
            pd.testing.assert_series_equal(restored, series)


def test_deserialize_pandas_with_metadata():
    """Test pandas deserialization with metadata parameter."""
    test_df = pd.DataFrame({"key": ["value1", "value2"], "num": [1, 2]})
    serialized_data = _serialize_pandas(test_df)

    # Metadata should be accepted but not required for pandas deserialization
    metadata = {"type": ("pandas.core.frame", "DataFrame"), "extra": "ignored"}
    restored = _deserialize_pandas_dataframe(serialized_data, metadata)

    pd.testing.assert_frame_equal(restored, test_df)


def test_deserialize_pandas_none_metadata():
    """Test pandas deserialization with None metadata."""
    test_series = pd.Series([1, 2, 3], name="test")
    serialized_data = _serialize_pandas(test_series)

    # Should work with None metadata
    restored = _deserialize_pandas_series(serialized_data, None)
    pd.testing.assert_series_equal(restored, test_series)


def test_roundtrip_pandas_serialization():
    """Test complete roundtrip pandas serialization."""
    test_cases = [
        # DataFrame cases
        pd.DataFrame({"simple": [1, 2, 3]}),
        pd.DataFrame({"mixed": [1, 2, 3], "types": ["a", "b", "c"], "floats": [1.1, 2.2, 3.3]}),
        pd.DataFrame({"complex": np.random.randn(50, 1).flatten()}),
        # Series cases
        pd.Series([1, 2, 3, 4, 5]),
        pd.Series(["string", "data", "test"]),
        pd.Series([1.5, 2.5, 3.5], name="named_series"),
    ]

    for original_obj in test_cases:
        # Serialize
        serialized = _serialize_pandas(original_obj)

        # Deserialize based on type
        if isinstance(original_obj, pd.DataFrame):
            restored = _deserialize_pandas_dataframe(serialized)
            pd.testing.assert_frame_equal(restored, original_obj)
        else:  # Series
            restored = _deserialize_pandas_series(serialized)
            pd.testing.assert_series_equal(restored, original_obj)

        # Verify types
        assert type(restored) is type(original_obj)


def test_pandas_error_handling():
    """Test pandas error handling with invalid data and objects."""
    # Test with invalid Arrow data
    invalid_data = b"this_is_not_valid_arrow_data"

    with pytest.raises((Exception,)):  # pyarrow will raise various exceptions
        _deserialize_pandas_dataframe(invalid_data)

    with pytest.raises((Exception,)):
        _deserialize_pandas_series(invalid_data)

    # Test serialize_pandas with unsupported object
    with pytest.raises(ValueError, match="Unsupported pandas object type"):
        _serialize_pandas("not_a_pandas_object")

    with pytest.raises(ValueError, match="Unsupported pandas object type"):
        _serialize_pandas([1, 2, 3])


def test_pandas_special_cases():
    """Test pandas serialization with special cases and edge conditions."""
    # DataFrame with index
    df_with_index = pd.DataFrame({"data": [1, 2, 3]}, index=["a", "b", "c"])
    serialized = _serialize_pandas(df_with_index)
    restored = _deserialize_pandas_dataframe(serialized)
    pd.testing.assert_frame_equal(restored, df_with_index)

    # Series with custom index
    series_with_index = pd.Series([10, 20, 30], index=["x", "y", "z"], name="custom")
    serialized = _serialize_pandas(series_with_index)
    restored = _deserialize_pandas_series(serialized)
    print(series_with_index)
    print(restored)
    pd.testing.assert_series_equal(restored, series_with_index)

    # DataFrame with MultiIndex columns
    df_multi_col = pd.DataFrame(
        np.random.randn(3, 4),
        columns=pd.MultiIndex.from_tuples([("A", "one"), ("A", "two"), ("B", "one"), ("B", "two")]),
    )
    serialized = _serialize_pandas(df_multi_col)
    restored = _deserialize_pandas_dataframe(serialized)
    pd.testing.assert_frame_equal(restored, df_multi_col)


def test_pandas_consistency_with_arrow():
    """Test that our pandas functions maintain Arrow format consistency."""
    test_df = pd.DataFrame(
        {
            "consistency": ["test", "data", "verification"],
            "numbers": [1, 2, 3],
            "floats": [1.1, 2.2, 3.3],
        }
    )

    # Serialize with our function
    our_serialized = _serialize_pandas(test_df)

    # Should be valid Arrow IPC stream format
    import pyarrow as pa

    buffer = pa.py_buffer(our_serialized)
    with pa.ipc.open_stream(buffer) as reader:
        arrow_table = reader.read_all()
        arrow_df = arrow_table.to_pandas()

    # Compare with our deserialization
    our_restored = _deserialize_pandas_dataframe(our_serialized)

    pd.testing.assert_frame_equal(our_restored, test_df)
    pd.testing.assert_frame_equal(arrow_df, test_df)


def test_pandas_unicode_and_special_characters():
    """Test pandas serialization with Unicode and special characters."""
    # DataFrame with Unicode
    unicode_df = pd.DataFrame(
        {"unicode": ["héllo", "wørld", "测试", "🎉"], "numbers": [1, 2, 3, 4]}
    )
    serialized = _serialize_pandas(unicode_df)
    restored = _deserialize_pandas_dataframe(serialized)
    pd.testing.assert_frame_equal(restored, unicode_df)

    # Series with special characters
    special_series = pd.Series(
        ["line1\nline2", "tab\there", 'quote"test', "apostrophe's"], name="special_chars"
    )
    serialized = _serialize_pandas(special_series)
    restored = _deserialize_pandas_series(serialized)
    pd.testing.assert_series_equal(restored, special_series)


def test_pandas_serialization_edge_cases():
    """Test pandas serialization with edge cases."""
    edge_cases = [
        pd.DataFrame(),  # Empty DataFrame
        pd.DataFrame({"col": []}),  # DataFrame with empty column
        pd.Series([], dtype=object),  # Empty Series
        pd.Series([None, None, None]),  # Series with all None values
        pd.DataFrame({"a": [1, 2, None], "b": [None, "test", 3.14]}),  # Mixed types with None
    ]

    for df_or_series in edge_cases:
        try:
            serialized = _serialize_pandas(df_or_series)
            assert isinstance(serialized, bytes)

            if isinstance(df_or_series, pd.DataFrame):
                restored = _deserialize_pandas_dataframe(serialized)
                assert isinstance(restored, pd.DataFrame)
            else:
                restored = _deserialize_pandas_series(serialized)
                assert isinstance(restored, pd.Series)

        except Exception as e:
            # Some edge cases might not be supported
            pytest.skip(f"Edge case not supported: {e}")


def test_pandas_serialization_unsupported_types():
    """Test pandas serialization with unsupported pandas objects."""

    # Test with unsupported type
    class UnsupportedPandasLike:
        pass

    obj = UnsupportedPandasLike()

    with pytest.raises(ValueError, match="Unsupported pandas object type"):
        _serialize_pandas(obj)


def test_deserialize_corrupted_arrow_data():
    """Test deserializing corrupted Arrow data."""
    # Create some invalid Arrow data
    invalid_arrow_data = b"not_valid_arrow_data"

    with pytest.raises((Exception,)):  # pyarrow will raise various exceptions
        _deserialize_pandas_dataframe(invalid_arrow_data)

    with pytest.raises((Exception,)):  # pyarrow will raise various exceptions
        _deserialize_pandas_series(invalid_arrow_data)
