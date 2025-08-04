# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""
Dynamically inject new Jupyter representation to some objects.
"""

from typing import Any, Optional

from jupyter_mimetypes._io import _deserialize
from jupyter_mimetypes._proxy import _MIMETYPES, _ProxyObject


def get_variable(
    name: str, mimetype: Optional[str] = None, globals_dict: Optional[dict] = None
) -> None:
    """
    Utility function to be used in kernel clients.

    This function retrieves a variable from the global namespace and displays
    it using the ProxyObject to enable custom MIME type serialization.

    Parameters
    ----------
    name : str
        The name of the variable to serialize.
    mimetype : str, optional
        The specific MIME type to include, by default None.
    globals_dict : dict, optional
        Dictionary containing variables to search for the named variable.
        If None, the function will not display anything, by default None.

    See Also
    --------
    serialize_object : Serialize an object directly without display.
    ProxyObject : The proxy class used for MIME bundle generation.

    Examples
    --------
    >>> _get_variable('my_dataframe', 'application/vnd.apache.arrow.stream')
    """
    from IPython.display import display

    include = None if mimetype is None else [mimetype]
    if globals_dict is not None:
        variable = globals_dict[name]
        proxy_var = _ProxyObject(variable)
        display(proxy_var, include=include)


def set_variable(
    name: str, data: dict[str, Any], metadata: dict[str, Any], globals_dict: dict[str, Any]
) -> None:
    """
    Utility function to set a variable in the kernel.

    This function deserializes MIME bundle data and sets the resulting object
    as a variable in the provided globals dictionary, enabling variable
    restoration in Jupyter kernel environments.

    Parameters
    ----------
    name : str
        The name of the variable to set in the globals dictionary.
    data : dict[str, str]
        A dictionary mapping MIME types to their serialized string representations.
    metadata : dict[str, Any]
        Additional metadata for deserialization containing type information.
    globals_dict : dict
        Dictionary to store the deserialized variable in.

    Returns
    -------
    None
        This function does not return a value; it modifies globals_dict in place.

    See Also
    --------
    get_variable : Retrieve a variable from the kernel.
    deserialize_object : Core deserialization function used internally.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'a': [1, 2, 3]})
    >>> data, metadata = serialize_object(df)
    >>> globals_dict = {}
    >>> set_variable('my_df', data, metadata, globals_dict)
    >>> isinstance(globals_dict['my_df'], pd.DataFrame)
    True
    """
    globals_dict[name] = deserialize_object(data=data, metadata=metadata)


def serialize_object(obj: Any, mimetype: Optional[str] = None) -> tuple[Any, Any]:
    """
    Utility function to serialize objects using custom MIME types.

    This function creates a ProxyObject wrapper around the input object
    and returns its MIME bundle representation.

    Parameters
    ----------
    obj : Any
        The object to serialize.
    mimetype : str, optional
        The specific MIME type to return, by default None.

    Returns
    -------
    tuple[dict[str, Any], dict[str, Any]] or tuple[Any, Any]
        If mimetype is None, returns (data, metadata) dictionaries.
        If mimetype is specified, returns the data and metadata for that type.

    See Also
    --------
    get_serialized_variable : Serialize a variable by name from globals.
    ProxyObject : The proxy class used for MIME bundle generation.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'a': [1, 2, 3]})
    >>> data, metadata = serialize_object(df)
    """
    proxy_obj = _ProxyObject(obj)
    data, metadata = proxy_obj._repr_mimebundle_()
    if mimetype is not None:
        return data[mimetype], metadata[mimetype]
    return data, metadata


def deserialize_object(data: dict[str, str], metadata: Optional[dict[str, Any]] = None) -> Any:
    """
    Deserialize an object from its string representation.

    This function takes serialized data in various MIME formats and reconstructs
    the original Python object using the appropriate deserialization method.

    Parameters
    ----------
    data : dict[str, str]
        A dictionary mapping MIME types to their serialized string representations.
    metadata : Optional[dict[str, Any]], optional
        Additional metadata for deserialization containing type information,
        by default None.

    Returns
    -------
    Any
        The deserialized Python object.

    See Also
    --------
    serialize_object : Serialize objects to MIME bundle format.
    deserialize : Core deserialization function.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'a': [1, 2, 3]})
    >>> data, metadata = serialize_object(df)
    >>> restored_df = deserialize_object(data, metadata)
    """
    metadata = {} if metadata is None else metadata
    for mimetype, string_obj in data.items():
        mod, var_type = metadata.get(mimetype, {}).get("type", (None, None))
        if mod and var_type:
            try:
                obj = _deserialize(
                    string_object=string_obj,
                    mimetypes=_MIMETYPES,
                    metadata=metadata,
                    mimetype=mimetype,
                )
                return obj
            except Exception as e:
                raise ValueError(f"Deserialization failed for {mimetype}: {e}") from e
    raise ValueError("No valid deserialization data found")


__all__ = [
    "deserialize_object",
    "get_variable",
    "serialize_object",
    "set_variable",
]
