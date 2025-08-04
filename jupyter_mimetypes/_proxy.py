# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""
Proxy objects for custom MIME type serialization in Jupyter environments.

This module provides proxy classes that wrap objects to enable custom
MIME type serialization for Jupyter's display system.
"""

from typing import Any, Optional

from jupyter_mimetypes._constants import (
    _DEFAULT_ARROW_MIMETYPE,
    _DEFAULT_PICKLE_MIMETYPE,
    _GENERIC_REPR_METHOD,
)
from jupyter_mimetypes._io import _serialize
from jupyter_mimetypes._io._pandas import (
    _deserialize_pandas_dataframe,
    _deserialize_pandas_series,
    _serialize_pandas,
)
from jupyter_mimetypes._io._pickle import _deserialize_pickle, _serialize_pickle
from jupyter_mimetypes._types import MIMETypeMapping
from jupyter_mimetypes._utils import _format_object, _get_serialized_type

_MIMETYPES: MIMETypeMapping = {
    # Mapping of (module, class) to (mimetype, serialize_func, deserialize_func)
    ("pandas.core.frame", "DataFrame"): (
        _DEFAULT_ARROW_MIMETYPE,
        _serialize_pandas,
        _deserialize_pandas_dataframe,
    ),
    ("pandas.core.series", "Series"): (
        _DEFAULT_ARROW_MIMETYPE,
        _serialize_pandas,
        _deserialize_pandas_series,
    ),
    ("*", "*"): (
        _DEFAULT_PICKLE_MIMETYPE,
        _serialize_pickle,
        _deserialize_pickle,
    ),
}


class _ProxyObject:
    """
    A generic proxy object that defines the _repr_mimebundle_ for the wrapped object.

    This class wraps any Python object and provides custom MIME type serialization
    capabilities through the _repr_mimebundle_ method, which is used by Jupyter's
    display system.

    Parameters
    ----------
    wrapped_object : Any
        The object to wrap with custom serialization capabilities.

    See Also
    --------
    serialize : Core serialization function used internally.
    format_object : Format objects using IPython's display formatters.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'a': [1, 2, 3]})
    >>> proxy = ProxyObject(df)
    >>> data, metadata = proxy._repr_mimebundle_()
    """

    def __init__(self, wrapped_object: Any):
        """
        Initialize the proxy object.

        This method initializes a ProxyObject that wraps another object
        to provide custom MIME type serialization capabilities.

        Parameters
        ----------
        wrapped_object : Any
            The object to wrap with custom serialization capabilities.

        See Also
        --------
        _repr_mimebundle_ : Generate MIME bundle representations.

        Examples
        --------
        >>> import pandas as pd
        >>> df = pd.DataFrame({'a': [1, 2, 3]})
        >>> proxy = ProxyObject(df)
        """
        self._wrapped = wrapped_object

    def _repr_mimebundle_(
        self, include: Optional[set[str]] = None, exclude: Optional[set[str]] = None
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Get the MIME bundle representation of the wrapped object.

        This method creates a MIME bundle containing multiple representations
        of the wrapped object, including custom serializations based on the
        object's type.

        Parameters
        ----------
        include : set[str], optional
            Set of MIME types to include, by default None.
        exclude : set[str], optional
            Set of MIME types to exclude, by default None.

        Returns
        -------
        tuple[dict[str, Any], dict[str, Any]]
            A tuple containing the formatted data and associated metadata.

        See Also
        --------
        format_object : Format objects using IPython's display formatters.
        serialize : Serialize objects to custom MIME types.

        Examples
        --------
        >>> import pandas as pd
        >>> df = pd.DataFrame({'a': [1, 2, 3]})
        >>> proxy = ProxyObject(df)
        >>> data, metadata = proxy._repr_mimebundle_()
        >>> 'application/vnd.apache.arrow.stream' in data
        True
        """
        obj = self._wrapped
        try:
            _old_repr = getattr(obj, _GENERIC_REPR_METHOD, None)
        except Exception:
            _old_repr = None

        data, metadata = (
            _format_object(obj, include=include, exclude=exclude)
            if _old_repr is None
            else _old_repr(include=include, exclude=exclude)
        )

        serialized, _mimetype_serialized = _serialize(
            obj=obj,
            mimetypes=_MIMETYPES,
        )
        if _mimetype_serialized not in data:
            data[_mimetype_serialized] = serialized

        metadata[_mimetype_serialized] = {"type": _get_serialized_type(obj)}
        if include is not None:
            for data_key in data.keys():
                if data_key not in include:
                    data.pop(data_key)
                    metadata.pop(data_key, None)

        if exclude is not None:
            for key in exclude:
                if key in data:
                    data.pop(key)
                    metadata.pop(key, None)

        return data, metadata
