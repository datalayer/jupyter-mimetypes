# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Constants for Jupyter MIME types and serialization."""

from jupyter_mimetypes._types import DeserializeFunc, MIMETypeMapping, SerializeFunc

_GENERIC_REPR_METHOD = "_repr_mimebundle_"
_DEFAULT_PICKLE_MIMETYPE = "application/x-python-pickle"
_DEFAULT_DILL_MIMETYPE = "application/x-python-dill"
_DEFAULT_ARROW_MIMETYPE = "application/vnd.apache.arrow.stream"


__all__ = [
    "_DEFAULT_ARROW_MIMETYPE",
    "_DEFAULT_DILL_MIMETYPE",
    "_DEFAULT_PICKLE_MIMETYPE",
    "_GENERIC_REPR_METHOD",
    "DeserializeFunc",
    "MIMETypeMapping",
    "SerializeFunc",
]
