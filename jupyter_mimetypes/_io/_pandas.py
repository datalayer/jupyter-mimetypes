# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Pandas integration for jupyter-mimetypes."""

from typing import Any, Optional

from jupyter_mimetypes._utils import _get_serialized_type


def _deserialize_pandas_dataframe(
    bytes_stream: bytes, metadata: Optional[dict[str, Any]] = None
) -> Any:
    """
    Deserialize bytes into a pandas DataFrame.

    This function converts Arrow IPC stream bytes back into a pandas DataFrame,
    preserving the original data structure and types.

    Parameters
    ----------
    bytes_stream : bytes
        The Arrow IPC stream data as bytes.
    metadata : Optional[dict[str, Any]], optional
        Additional metadata for deserialization, by default None.

    Returns
    -------
    pd.DataFrame
        The deserialized pandas DataFrame.

    See Also
    --------
    _serialize_pandas : Serialize pandas objects to Arrow IPC format.
    _deserialize_pandas_series : Deserialize bytes to pandas Series.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    >>> serialized = _serialize_pandas(df)
    >>> restored = _deserialize_pandas_dataframe(serialized)
    >>> isinstance(restored, pd.DataFrame)
    True
    """
    import pyarrow as pa

    buffer = pa.py_buffer(bytes_stream)
    with pa.ipc.open_stream(buffer) as reader:
        return reader.read_pandas()  # type: ignore


def _deserialize_pandas_series(
    bytes_stream: bytes, metadata: Optional[dict[str, Any]] = None
) -> Any:
    """
    Deserialize bytes into a pandas Series.

    This function converts Arrow IPC stream bytes back into a pandas Series,
    preserving the original data structure and types.

    Parameters
    ----------
    bytes_stream : bytes
        The Arrow IPC stream data as bytes.
    metadata : Optional[dict[str, Any]], optional
        Additional metadata for deserialization, by default None.

    Returns
    -------
    pd.Series
        The deserialized pandas Series.

    See Also
    --------
    _serialize_pandas : Serialize pandas objects to Arrow IPC format.
    _deserialize_pandas_dataframe : Deserialize bytes to pandas DataFrame.

    Examples
    --------
    >>> import pandas as pd
    >>> series = pd.Series([1, 2, 3], name='test')
    >>> serialized = _serialize_pandas(series)
    >>> restored = _deserialize_pandas_series(serialized)
    >>> isinstance(restored, pd.Series)
    True
    """
    dataframe = _deserialize_pandas_dataframe(bytes_stream, metadata)
    series_name = dataframe.columns[0]
    series = dataframe.get(series_name)
    return series


def _serialize_pandas(pandas_obj: Any) -> bytes:
    """
    Convert a pandas DataFrame or Series to an Arrow IPC stream.

    This function serializes pandas objects using Apache Arrow's IPC format,
    which provides efficient cross-language data interchange capabilities.

    Parameters
    ----------
    pandas_obj : pd.DataFrame or pd.Series
        The pandas object to convert.

    Returns
    -------
    bytes
        The Arrow IPC stream as bytes.

    See Also
    --------
    deserialize_pandas : Convert Arrow IPC format back to pandas objects.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    >>> serialized = serialize_pandas(df)
    >>> isinstance(serialized, bytes)
    True
    """
    import pyarrow as pa

    table = None
    _mod, var_type = _get_serialized_type(pandas_obj)
    if var_type == "Series":
        if pandas_obj.name is None:
            pandas_obj.name = "None"

        table = pa.Table.from_pandas(pandas_obj.to_frame(name=pandas_obj.name), preserve_index=True)
        # table = pa.Table.from_arrays(
        #     [pa.Array.from_pandas(pandas_obj)], names=[str(pandas_obj.name)]
        # )
    elif var_type == "DataFrame":
        table = pa.Table.from_pandas(pandas_obj)

    if table is not None:
        sink = pa.BufferOutputStream()
        with pa.ipc.new_stream(sink, table.schema) as writer:
            writer.write_table(table)

        buffer = sink.getvalue()
        return buffer.to_pybytes()

    raise ValueError(f"Unsupported pandas object type: {type(pandas_obj)}")
