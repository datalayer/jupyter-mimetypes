# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Pickle integration for jupyter-mimetypes."""

import pickle
from typing import Any, Optional


def _deserialize_pickle(data: bytes, metadata: Optional[dict[str, Any]] = None) -> Any:
    """
    Deserialize a Python object from its bytes representation.

    This function uses pickle.loads to deserialize Python objects from their
    byte representation. Note that pickle can execute arbitrary code, so only
    deserialize data from trusted sources.

    Parameters
    ----------
    data : bytes
        The serialized object as bytes.
    metadata : Optional[dict[str, Any]], optional
        Additional metadata for deserialization, by default None.

    Returns
    -------
    Any
        The deserialized object.

    See Also
    --------
    serialize_pickle : Serialize objects to pickle format.

    Examples
    --------
    >>> import pickle
    >>> data = pickle.dumps([1, 2, 3])
    >>> deserialize_pickle(data)
    [1, 2, 3]
    """
    return pickle.loads(data)  # noqa: S301


def _serialize_pickle(obj: Any) -> bytes:
    """
    Serialize a Python object to a bytes representation.

    This function uses pickle.dumps to serialize arbitrary Python objects
    to a binary format that can be stored or transmitted.

    Parameters
    ----------
    obj : Any
        The object to serialize.

    Returns
    -------
    bytes
        The serialized object as bytes.

    See Also
    --------
    deserialize_pickle : Deserialize objects from pickle format.

    Examples
    --------
    >>> data = serialize_pickle([1, 2, 3])
    >>> isinstance(data, bytes)
    True
    """
    return pickle.dumps(obj)
