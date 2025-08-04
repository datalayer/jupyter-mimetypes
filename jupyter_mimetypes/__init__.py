# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""
Dynamically inject new Jupyter representation to some objects.
"""

from jupyter_mimetypes.api import deserialize_object, get_variable, serialize_object, set_variable

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "deserialize_object",
    "get_variable",
    "serialize_object",
    "set_variable",
]
