# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Common utilities for jupyter-mimetypes."""

import binascii
from typing import Any, Optional, Union

from jupyter_mimetypes._constants import _DEFAULT_PICKLE_MIMETYPE
from jupyter_mimetypes._io._pickle import _deserialize_pickle, _serialize_pickle
from jupyter_mimetypes._types import DeserializeFunc, MIMETypeMapping, SerializeFunc


def _get_serialized_type(variable: Any) -> tuple[Union[str, None], str]:
    """
    Serialize a Python object as tuple[module, name].

    This function extracts the module name and qualified name from a Python
    object, which is useful for type identification in serialization.

    Parameters
    ----------
    variable : Any
        The Python type to serialize.

    Returns
    -------
    tuple[Union[str, None], str]
        A tuple containing the module name (or None) and the qualified name.

    See Also
    --------
    _patch_repr_with_arrow : Function that uses this serialization.

    Examples
    --------
    >>> import pandas as pd
    >>> _get_serialized_type(pd.DataFrame)
    ('pandas.core.frame', 'DataFrame')
    """
    variable_type = type(variable)
    return (
        getattr(variable_type, "__module__", None),
        variable_type.__qualname__,
    )


def _format_object(
    obj: Any,
    include: Union[set[str], None] = None,
    exclude: Union[set[str], None] = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Format an object using IPython's display formatters.

    This function uses IPython's display formatter system to convert objects
    into various MIME type representations.

    Parameters
    ----------
    obj : Any
        The object to format.
    include : Union[set[str], None], optional
        Set of MIME types to include, by default None (all types).
    exclude : Union[set[str], None], optional
        Set of MIME types to exclude, by default None.

    Returns
    -------
    tuple[dict[str, Any], dict[str, Any]]
        A tuple containing (format_dict, metadata_dict) where format_dict
        contains the formatted representations and metadata_dict contains
        associated metadata.

    See Also
    --------
    _patch_repr_with_arrow : Function that uses this for object formatting.

    Examples
    --------
    >>> data, metadata = format_object("hello")
    >>> "text/plain" in data
    True
    """
    from IPython.core.interactiveshell import InteractiveShell

    # if not InteractiveShell.initialized():
    #     return {}, {}
    format_dict = {}
    md_dict = {}

    display_formatter = InteractiveShell.instance().display_formatter
    if display_formatter is None:
        return {}, {}

    for format_type, formatter in display_formatter.formatters.items():
        if include and format_type not in include:
            continue
        if exclude and format_type in exclude:
            continue

        md = None
        data = formatter(obj)

        # formatters can return raw data or (data, metadata)
        if isinstance(data, tuple) and len(data) == 2:
            data, md = data

        if data is not None:
            format_dict[format_type] = data
        if md is not None:
            md_dict[format_type] = md

    return format_dict, md_dict


def _from_b64(data: str, encoding: str = "utf-8") -> bytes:
    """
    Convert a base64-encoded string to binary data.

    This function decodes a base64-encoded string back to its original
    binary representation using the specified encoding.

    Parameters
    ----------
    data : str
        The base64-encoded string to decode.
    encoding : str, optional
        The encoding to use for the input string, by default "utf-8".

    Returns
    -------
    bytes
        The decoded binary data.

    See Also
    --------
    to_b64 : Convert binary data to base64-encoded string.

    Examples
    --------
    >>> encoded = "SGVsbG8gV29ybGQ="
    >>> decoded = from_b64(encoded)
    >>> decoded.decode('utf-8')
    'Hello World'
    """
    return binascii.a2b_base64(data.encode(encoding))


def _to_b64(data: bytes, encoding: str = "utf-8") -> str:
    """
    Convert binary data to a base64-encoded string.

    This function encodes binary data as a base64 string, which is useful
    for transmitting binary data over text-based protocols.

    Parameters
    ----------
    data : bytes
        The binary data to encode.
    encoding : str, optional
        The encoding to use for the output string, by default "utf-8".

    Returns
    -------
    str
        A base64-encoded string representation of the input data.

    See Also
    --------
    from_b64 : Convert base64-encoded string back to binary data.

    Examples
    --------
    >>> data = b"Hello World"
    >>> encoded = to_b64(data)
    >>> encoded.strip()
    'SGVsbG8gV29ybGQ='
    """
    return binascii.b2a_base64(data).decode(encoding)


def _get_mimetype_funcs_for_obj(
    obj: Any, mimetypes: dict[tuple[str, str], Any]
) -> tuple[Optional[str], Optional[SerializeFunc], Optional[DeserializeFunc]]:
    """
    Get the preferred MIME type and serialization functions for a given object.

    This function looks up the appropriate MIME type and associated
    serialization/deserialization functions for an object based on its
    module and class name.

    Parameters
    ----------
    obj : Any
        The object for which to get the MIME type and functions.
    mimetypes : dict[tuple[str, str], Any]
        A mapping of (module, class) to (mimetype, serialize_func, deserialize_func).

    Returns
    -------
    tuple[Optional[str], Optional[Callable[..., bytes]], Optional[Callable[..., Any]]]
        A tuple containing the MIME type, serialization function, and
        deserialization function, or (None, None, None) if not found.

    See Also
    --------
    get_serialized_type : Get module and class name for an object.
    serialize : Serialize objects using these functions.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'a': [1, 2, 3]})
    >>> mimetype, serialize_func, deserialize_func = get_mimetype_funcs_for_obj(df, MIMETYPES)
    """
    mod, var_type = _get_serialized_type(obj)
    return _get_mimetypes_funcs_for_mod_type(mod, var_type, mimetypes=mimetypes)


def _get_mimetypes_funcs_for_mod_type(
    mod: Optional[str], var_type: str, mimetypes: MIMETypeMapping
) -> tuple[Optional[str], Optional[SerializeFunc], Optional[DeserializeFunc]]:
    """
    Get the MIME type and serialization functions for a given module and variable type.

    This function looks up the appropriate MIME type and associated
    serialization/deserialization functions for a module and variable type
    based on the provided mimetypes mapping.

    Parameters
    ----------
    mod : Optional[str]
        The module name to look up.
    var_type : str
        The variable type to look up.
    mimetypes : dict[tuple[str, str], Any]
        A mapping of (module, class) to (mimetype, serialize_func, deserialize_func).

    Returns
    -------
    tuple[Optional[str], Optional[Callable[..., bytes]], Optional[Callable[..., Any]]]
        A tuple containing the MIME type, serialization function, and
        deserialization function, or (None, None, None) if not found.

    See Also
    --------
    get_mimetype_funcs_for_obj : Get functions for a specific object.
    get_serialized_type : Get module and class name for an object.

    Examples
    --------
    >>> MIMETYPES = {
    ...     ('pandas.core.frame', 'DataFrame'): (
    ...         'application/vnd.apache.arrow.stream', serialize_pandas, deserialize_pandas
    ...     )
    ... }
    >>> mimetype, serialize_func, deserialize_func = get_mimetypes_funcs_for_mod_type(
    ...     'pandas.core.frame', 'DataFrame', MIMETYPES
    ... )
    """
    if mod and var_type:
        for key, value in mimetypes.items():
            _mod, _type = key
            if _mod in [mod, "*"] and _type in [var_type, "*"]:
                return value
    return (_DEFAULT_PICKLE_MIMETYPE, _serialize_pickle, _deserialize_pickle)
