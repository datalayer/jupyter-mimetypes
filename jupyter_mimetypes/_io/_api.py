# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Serialization and deserialization functions for jupyter-mimetypes."""

from typing import Any, Optional

from jupyter_mimetypes._constants import _DEFAULT_PICKLE_MIMETYPE
from jupyter_mimetypes._types import MIMETypeMapping
from jupyter_mimetypes._utils import (
    _from_b64,
    _get_mimetype_funcs_for_obj,
    _get_mimetypes_funcs_for_mod_type,
    _to_b64,
)


def _serialize(
    obj: Any,
    mimetypes: MIMETypeMapping,
) -> tuple[str, str]:
    """
    Serialize an object to a binary format.

    This function determines the appropriate serialization method for an object
    based on its type and the provided MIME type mappings, then serializes
    the object accordingly.

    Parameters
    ----------
    obj : Any
        The object to serialize.
    mimetypes : dict[tuple[str, str], Any]
        A mapping of (module, class) to (mimetype, serialize_func, deserialize_func).

    Returns
    -------
    tuple[str, str]
        A tuple containing the base64-encoded serialized data and the MIME type used.

    See Also
    --------
    deserialize : Deserialize objects from binary format.
    get_mimetype_funcs_for_obj : Get serialization functions for an object.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'a': [1, 2, 3]})
    >>> data, mimetype = serialize(df, MIMETYPES)
    """
    default_mimetype, serialize_func, _ = _get_mimetype_funcs_for_obj(obj, mimetypes=mimetypes)
    if serialize_func is None or default_mimetype is None:
        raise ValueError(f"Unsupported object: {obj}")
    try:
        serialized_result = serialize_func(obj)
        # Ensure we have bytes for base64 encoding
        if isinstance(serialized_result, str):
            serialized_bytes = serialized_result.encode("utf-8")
        else:
            serialized_bytes = serialized_result
        return _to_b64(serialized_bytes), default_mimetype
    except Exception as e:
        raise ValueError(f"Serialization failed for {default_mimetype}: {e}") from e


def _deserialize(
    string_object: str,
    mimetypes: MIMETypeMapping,
    metadata: dict[str, Any],
    mimetype: Optional[str] = None,
) -> Any:
    """
    Deserialize an object from a binary format.

    This function takes serialized data and reconstructs the original object
    using the appropriate deserialization function based on the MIME type.

    Parameters
    ----------
    string_object : str
        The base64-encoded string to decode.
    mimetypes : MIMETypeMapping
        A mapping of MIME types to deserialization functions.
    metadata : dict[str, Any]
        Metadata to pass to the deserialization function.
    mimetype : str, optional
        The MIME type of the data, by default None.

    Returns
    -------
    Any
        The deserialized object.

    See Also
    --------
    _serialize : Serialize objects to binary format.
    _from_b64 : Decode base64 strings to bytes.

    Notes
    -----
    In some cases, the metadata may be used to determine the correct
    deserialization function, so unless the mimetype maps to unique
    deserialization functions, it is recommended to provide metadata.

    Examples
    --------
    >>> serialized_data = "base64_encoded_data"
    >>> obj = _deserialize(
    ...     serialized_data,
    ...     MIMETYPES,
    ...     {},
    ...     "application/vnd.apache.arrow.stream"
    ... )
    """
    metadata = metadata or {}
    mimetype = mimetype if mimetype is not None else _DEFAULT_PICKLE_MIMETYPE
    mod, var_type = metadata.get(mimetype, {}).get("type", (None, None))
    _, _, deserialization_func = _get_mimetypes_funcs_for_mod_type(
        mod, var_type, mimetypes=mimetypes
    )
    if deserialization_func is None:
        raise ValueError(f"Unsupported mimetype: {mimetype}")
    else:
        try:
            return deserialization_func(_from_b64(string_object), metadata=metadata)
        except Exception as e:
            raise ValueError(f"Deserialization failed for {mimetype}: {e}") from e
