# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Serialization and deserialization module for jupyter-mimetypes."""

from jupyter_mimetypes._io._api import _deserialize, _serialize

__all__ = ["_deserialize", "_serialize"]
